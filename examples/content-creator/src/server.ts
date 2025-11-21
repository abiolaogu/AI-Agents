/**
 * Content Creator AI Agent
 * Multi-format content generation for marketing and media
 *
 * Scale: 5K concurrent, 100K+ pieces/day
 * Tech: TypeScript, Node.js, Express, Claude 3.5 Sonnet
 */

import express, { Request, Response } from 'express';
import Anthropic from '@anthropic-ai/sdk';
import Redis from 'ioredis';
import { promisify } from 'util';
import * as prometheus from 'prom-client';

// Configuration
interface Config {
  appName: string;
  version: string;
  port: number;
  redisUrl: string;
  claudeApiKey: string;
  claudeModel: string;
}

const config: Config = {
  appName: 'content-creator',
  version: '1.0.0',
  port: parseInt(process.env.PORT || '8088'),
  redisUrl: process.env.REDIS_URL || 'redis://localhost:6379',
  claudeApiKey: process.env.CLAUDE_API_KEY || 'your-api-key-here',
  claudeModel: 'claude-3-5-sonnet-20241022',
};

// Metrics
const contentGeneratedCounter = new prometheus.Counter({
  name: 'content_creator_generated_total',
  help: 'Total content pieces generated',
  labelNames: ['content_type', 'platform'],
});

const generationDuration = new prometheus.Histogram({
  name: 'content_creator_generation_duration_seconds',
  help: 'Content generation duration',
  labelNames: ['content_type'],
});

const wordCount = new prometheus.Histogram({
  name: 'content_creator_word_count',
  help: 'Generated content word count',
  buckets: [50, 100, 250, 500, 1000, 2000, 5000],
});

prometheus.collectDefaultMetrics();

// Data Models
enum ContentType {
  BLOG_POST = 'blog_post',
  SOCIAL_MEDIA = 'social_media',
  VIDEO_SCRIPT = 'video_script',
  EMAIL = 'email',
  PRODUCT_DESC = 'product_description',
  AD_COPY = 'ad_copy',
}

enum Platform {
  TWITTER = 'twitter',
  LINKEDIN = 'linkedin',
  INSTAGRAM = 'instagram',
  FACEBOOK = 'facebook',
  TIKTOK = 'tiktok',
  YOUTUBE = 'youtube',
  BLOG = 'blog',
  EMAIL = 'email',
}

enum Tone {
  PROFESSIONAL = 'professional',
  CASUAL = 'casual',
  FRIENDLY = 'friendly',
  AUTHORITATIVE = 'authoritative',
  HUMOROUS = 'humorous',
  INSPIRATIONAL = 'inspirational',
}

interface ContentRequest {
  requestId?: string;
  contentType: ContentType;
  platform?: Platform;
  topic: string;
  keywords?: string[];
  targetAudience?: string;
  tone?: Tone;
  wordCount?: number;
  brandVoice?: string;
  seoOptimized?: boolean;
  includeHashtags?: boolean;
  includeCTA?: boolean;
}

interface ContentResponse {
  requestId: string;
  content: string;
  headline?: string;
  subheadings?: string[];
  hashtags?: string[];
  metadata: {
    wordCount: number;
    characterCount: number;
    readingTime: number; // minutes
    seoScore?: number;
  };
  suggestions: string[];
  generationTimeMs: number;
}

// Services
class ContentGenerator {
  private claude: Anthropic;
  private redis: Redis;

  constructor(apiKey: string, redisClient: Redis) {
    this.claude = new Anthropic({ apiKey });
    this.redis = redisClient;
  }

  async generateContent(req: ContentRequest): Promise<ContentResponse> {
    const startTime = Date.now();
    const timer = generationDuration.startTimer({ content_type: req.contentType });

    try {
      // Build prompt based on content type
      const prompt = this.buildPrompt(req);

      // Generate content using Claude
      const response = await this.claude.messages.create({
        model: config.claudeModel,
        max_tokens: this.getMaxTokens(req.contentType, req.wordCount),
        messages: [{
          role: 'user',
          content: prompt,
        }],
      });

      const generatedText = response.content[0].type === 'text'
        ? response.content[0].text
        : '';

      // Parse the response
      const parsed = this.parseGeneratedContent(generatedText, req);

      // Generate metadata
      const metadata = {
        wordCount: this.countWords(parsed.content),
        characterCount: parsed.content.length,
        readingTime: Math.ceil(this.countWords(parsed.content) / 200), // 200 wpm
      };

      if (req.seoOptimized) {
        metadata.seoScore = this.calculateSEOScore(parsed.content, req.keywords || []);
      }

      // Track metrics
      wordCount.observe(metadata.wordCount);
      contentGeneratedCounter.inc({
        content_type: req.contentType,
        platform: req.platform || 'generic',
      });

      const result: ContentResponse = {
        requestId: req.requestId || `content_${Date.now()}`,
        content: parsed.content,
        headline: parsed.headline,
        subheadings: parsed.subheadings,
        hashtags: parsed.hashtags,
        metadata,
        suggestions: await this.generateSuggestions(req, parsed.content),
        generationTimeMs: Date.now() - startTime,
      };

      // Cache result
      await this.cacheResult(result.requestId, result);

      return result;
    } finally {
      timer();
    }
  }

  private buildPrompt(req: ContentRequest): string {
    const parts: string[] = [];

    // Content type specific instructions
    switch (req.contentType) {
      case ContentType.BLOG_POST:
        parts.push(`Write a comprehensive blog post about: ${req.topic}`);
        if (req.wordCount) {
          parts.push(`Target word count: ${req.wordCount} words`);
        }
        if (req.seoOptimized) {
          parts.push(`SEO-optimize for keywords: ${req.keywords?.join(', ')}`);
        }
        break;

      case ContentType.SOCIAL_MEDIA:
        parts.push(`Create a ${req.platform} post about: ${req.topic}`);
        if (req.platform === Platform.TWITTER) {
          parts.push('Keep it under 280 characters');
        } else if (req.platform === Platform.LINKEDIN) {
          parts.push('Professional tone, 150-300 words');
        } else if (req.platform === Platform.INSTAGRAM) {
          parts.push('Engaging caption with emojis, 125-150 words');
        }
        break;

      case ContentType.VIDEO_SCRIPT:
        parts.push(`Write a video script about: ${req.topic}`);
        if (req.platform === Platform.YOUTUBE) {
          parts.push('Include intro hook, main content, and CTA');
        } else if (req.platform === Platform.TIKTOK) {
          parts.push('Keep it under 60 seconds, fast-paced');
        }
        break;

      case ContentType.EMAIL:
        parts.push(`Write an email about: ${req.topic}`);
        parts.push('Include subject line, body, and call-to-action');
        break;

      case ContentType.PRODUCT_DESC:
        parts.push(`Write a product description for: ${req.topic}`);
        parts.push('Highlight features, benefits, and unique selling points');
        break;

      case ContentType.AD_COPY:
        parts.push(`Write ad copy for: ${req.topic}`);
        parts.push('Platform: ${req.platform || "multi-platform"}');
        parts.push('Include attention-grabbing headline and persuasive body');
        break;
    }

    // Common requirements
    if (req.tone) {
      parts.push(`Tone: ${req.tone}`);
    }

    if (req.targetAudience) {
      parts.push(`Target audience: ${req.targetAudience}`);
    }

    if (req.brandVoice) {
      parts.push(`Brand voice: ${req.brandVoice}`);
    }

    if (req.includeHashtags) {
      parts.push('Include 5-10 relevant hashtags');
    }

    if (req.includeCTA) {
      parts.push('Include a strong call-to-action');
    }

    // Response format
    parts.push('\nProvide the response in JSON format:');
    parts.push(JSON.stringify({
      content: 'main content here',
      headline: 'headline if applicable',
      subheadings: ['subheading 1', 'subheading 2'],
      hashtags: ['hashtag1', 'hashtag2'],
    }, null, 2));

    return parts.join('\n');
  }

  private getMaxTokens(contentType: ContentType, wordCount?: number): number {
    if (wordCount) {
      return Math.ceil(wordCount * 1.5); // ~1.5 tokens per word
    }

    switch (contentType) {
      case ContentType.BLOG_POST:
        return 3000;
      case ContentType.SOCIAL_MEDIA:
        return 500;
      case ContentType.VIDEO_SCRIPT:
        return 2000;
      case ContentType.EMAIL:
        return 1000;
      case ContentType.PRODUCT_DESC:
        return 800;
      case ContentType.AD_COPY:
        return 500;
      default:
        return 2000;
    }
  }

  private parseGeneratedContent(text: string, req: ContentRequest): {
    content: string;
    headline?: string;
    subheadings?: string[];
    hashtags?: string[];
  } {
    try {
      // Try to parse as JSON
      const jsonMatch = text.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        return {
          content: parsed.content || text,
          headline: parsed.headline,
          subheadings: parsed.subheadings || [],
          hashtags: parsed.hashtags || [],
        };
      }
    } catch (e) {
      // Fallback to text parsing
    }

    // Extract hashtags from text
    const hashtags = text.match(/#\w+/g) || [];

    return {
      content: text,
      hashtags: hashtags.length > 0 ? hashtags : undefined,
    };
  }

  private countWords(text: string): number {
    return text.trim().split(/\s+/).length;
  }

  private calculateSEOScore(content: string, keywords: string[]): number {
    if (keywords.length === 0) return 50;

    let score = 50;
    const lowerContent = content.toLowerCase();

    // Keyword presence
    const keywordsFound = keywords.filter(kw =>
      lowerContent.includes(kw.toLowerCase())
    );
    score += (keywordsFound.length / keywords.length) * 30;

    // Content length
    const wordCount = this.countWords(content);
    if (wordCount >= 300 && wordCount <= 2500) {
      score += 10;
    }

    // Readability (simplified)
    const avgWordLength = content.length / wordCount;
    if (avgWordLength >= 4 && avgWordLength <= 6) {
      score += 10;
    }

    return Math.min(100, Math.round(score));
  }

  private async generateSuggestions(req: ContentRequest, content: string): Promise<string[]> {
    const suggestions: string[] = [];

    // Platform-specific suggestions
    if (req.platform === Platform.TWITTER) {
      suggestions.push('Consider creating a thread for more detailed content');
      suggestions.push('Add relevant Twitter handles to increase visibility');
    } else if (req.platform === Platform.LINKEDIN) {
      suggestions.push('Add relevant LinkedIn hashtags to increase reach');
      suggestions.push('Tag relevant companies or people');
    } else if (req.platform === Platform.INSTAGRAM) {
      suggestions.push('Pair with high-quality visuals or carousel');
      suggestions.push('Post during peak engagement hours (11am-1pm, 7pm-9pm)');
    }

    // General suggestions
    if (!req.includeHashtags && req.contentType === ContentType.SOCIAL_MEDIA) {
      suggestions.push('Consider adding hashtags for better discoverability');
    }

    if (this.countWords(content) < 300 && req.contentType === ContentType.BLOG_POST) {
      suggestions.push('Consider expanding content to 500+ words for better SEO');
    }

    return suggestions;
  }

  private async cacheResult(requestId: string, result: ContentResponse): Promise<void> {
    try {
      await this.redis.setex(
        `content:${requestId}`,
        24 * 60 * 60, // 24 hours
        JSON.stringify(result)
      );
    } catch (error) {
      console.error('Failed to cache result:', error);
    }
  }
}

// HTTP Server
class ContentCreatorServer {
  private app: express.Application;
  private contentGenerator: ContentGenerator;
  private redis: Redis;

  constructor() {
    this.app = express();
    this.redis = new Redis(config.redisUrl);
    this.contentGenerator = new ContentGenerator(config.claudeApiKey, this.redis);
    this.setupMiddleware();
    this.setupRoutes();
  }

  private setupMiddleware(): void {
    this.app.use(express.json());
    this.app.use(express.urlencoded({ extended: true }));

    // Logging middleware
    this.app.use((req, res, next) => {
      console.log(`${new Date().toISOString()} ${req.method} ${req.path}`);
      next();
    });
  }

  private setupRoutes(): void {
    this.app.get('/health', this.healthCheck.bind(this));
    this.app.get('/metrics', this.metrics.bind(this));
    this.app.post('/api/v1/generate', this.generateContent.bind(this));
    this.app.get('/', this.root.bind(this));
  }

  private healthCheck(req: Request, res: Response): void {
    res.json({
      status: 'healthy',
      service: config.appName,
      version: config.version,
      timestamp: new Date().toISOString(),
    });
  }

  private metrics(req: Request, res: Response): void {
    res.set('Content-Type', prometheus.register.contentType);
    res.end(prometheus.register.metrics());
  }

  private async generateContent(req: Request, res: Response): Promise<void> {
    try {
      const contentReq: ContentRequest = req.body;

      // Validate request
      if (!contentReq.contentType || !contentReq.topic) {
        res.status(400).json({
          error: 'Missing required fields: contentType and topic',
        });
        return;
      }

      const result = await this.contentGenerator.generateContent(contentReq);
      res.json(result);
    } catch (error) {
      console.error('Content generation error:', error);
      res.status(500).json({
        error: error instanceof Error ? error.message : 'Internal server error',
      });
    }
  }

  private root(req: Request, res: Response): void {
    res.json({
      service: config.appName,
      version: config.version,
      status: 'operational',
      documentation: '/docs',
    });
  }

  public start(): void {
    this.app.listen(config.port, () => {
      console.log(`${config.appName} v${config.version} listening on port ${config.port}`);
    });
  }
}

// Start server
const server = new ContentCreatorServer();
server.start();

export { ContentCreatorServer, ContentGenerator };
