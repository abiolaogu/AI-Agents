"""
Financial Forecaster AI Agent
Time-series prediction, risk modeling, and portfolio optimization.

Scale: Real-time streaming data, 100K securities
Tech: Python, FastAPI, Claude 3.5 Sonnet, Prophet, TensorFlow, Redis, TimescaleDB
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import numpy as np
import pandas as pd

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import anthropic
from prophet import Prophet
import tensorflow as tf
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    APP_NAME = "financial-forecaster"
    VERSION = "1.0.0"
    PORT = 8083
    CLAUDE_API_KEY = "your-api-key-here"
    CLAUDE_MODEL = "claude-3-5-sonnet-20241022"
    FORECAST_HORIZON_DAYS = 30
    CONFIDENCE_INTERVAL = 0.95

config = Config()

# ============================================================================
# METRICS
# ============================================================================

forecast_counter = Counter('financial_forecaster_requests_total', 'Total forecast requests', ['type'])
forecast_duration = Histogram('financial_forecaster_duration_seconds', 'Forecast duration')
model_accuracy = Histogram('financial_forecaster_accuracy', 'Forecast accuracy (MAPE)')

# ============================================================================
# DATA MODELS
# ============================================================================

class TimeSeriesData(BaseModel):
    """Time series data point"""
    timestamp: datetime
    value: float

class ForecastRequest(BaseModel):
    """Forecast request"""
    security_id: str = Field(..., description="Security identifier (ticker symbol)")
    historical_data: List[TimeSeriesData] = Field(..., min_items=30)
    forecast_horizon_days: int = Field(default=30, ge=1, le=365)
    include_analysis: bool = Field(default=False)

class ForecastResponse(BaseModel):
    """Forecast response"""
    security_id: str
    forecast: List[Dict[str, Any]]
    confidence_intervals: List[Dict[str, Any]]
    trend: str  # "bullish", "bearish", "neutral"
    risk_score: float = Field(..., ge=0, le=100)
    claude_analysis: Optional[str] = None
    recommendations: List[str]
    processing_time_ms: float

class PortfolioOptimizationRequest(BaseModel):
    """Portfolio optimization request"""
    securities: List[str]
    investment_amount: float
    risk_tolerance: str = Field(..., pattern="^(low|medium|high)$")
    constraints: Optional[Dict[str, Any]] = None

class PortfolioOptimizationResponse(BaseModel):
    """Portfolio optimization response"""
    allocations: Dict[str, float]
    expected_return: float
    expected_risk: float
    sharpe_ratio: float
    recommendations: List[str]

# ============================================================================
# SERVICES
# ============================================================================

class ForecastingService:
    """Time-series forecasting service"""

    def __init__(self):
        self.prophet_models = {}
        self.lstm_models = {}

    async def forecast_prophet(self, data: List[TimeSeriesData], horizon: int) -> Dict:
        """Forecast using Prophet (Facebook's time series model)"""
        try:
            # Prepare data for Prophet
            df = pd.DataFrame([
                {"ds": d.timestamp, "y": d.value}
                for d in data
            ])

            # Train Prophet model
            model = Prophet(
                changepoint_prior_scale=0.05,
                seasonality_mode='multiplicative',
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False
            )
            model.fit(df)

            # Generate forecast
            future = model.make_future_dataframe(periods=horizon)
            forecast = model.predict(future)

            # Extract results
            forecast_data = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(horizon)

            return {
                "forecast": [
                    {
                        "date": row['ds'].isoformat(),
                        "predicted_value": float(row['yhat']),
                        "lower_bound": float(row['yhat_lower']),
                        "upper_bound": float(row['yhat_upper'])
                    }
                    for _, row in forecast_data.iterrows()
                ],
                "model": "prophet"
            }

        except Exception as e:
            logger.error(f"Prophet forecasting error: {e}")
            raise

    async def forecast_lstm(self, data: List[TimeSeriesData], horizon: int) -> Dict:
        """Forecast using LSTM neural network"""
        try:
            # Prepare data
            values = np.array([d.value for d in data])

            # Normalize
            mean = np.mean(values)
            std = np.std(values)
            normalized = (values - mean) / std if std > 0 else values

            # Create sequences
            sequence_length = 30
            X = []
            for i in range(len(normalized) - sequence_length):
                X.append(normalized[i:i+sequence_length])
            X = np.array(X)

            # Build simple LSTM model (simplified for demo)
            # In production, use pre-trained model
            model = tf.keras.Sequential([
                tf.keras.layers.LSTM(50, activation='relu', input_shape=(sequence_length, 1)),
                tf.keras.layers.Dense(1)
            ])
            model.compile(optimizer='adam', loss='mse')

            # Predict (using last sequence)
            if len(X) > 0:
                last_sequence = X[-1].reshape(1, sequence_length, 1)
                predictions = []
                current_sequence = last_sequence

                for _ in range(horizon):
                    pred = model.predict(current_sequence, verbose=0)
                    predictions.append(pred[0, 0])
                    # Update sequence
                    current_sequence = np.roll(current_sequence, -1)
                    current_sequence[0, -1, 0] = pred[0, 0]

                # Denormalize
                predictions = np.array(predictions) * std + mean

                return {
                    "forecast": [
                        {
                            "date": (data[-1].timestamp + timedelta(days=i+1)).isoformat(),
                            "predicted_value": float(pred),
                            "model": "lstm"
                        }
                        for i, pred in enumerate(predictions)
                    ],
                    "model": "lstm"
                }
            else:
                raise ValueError("Insufficient data for LSTM")

        except Exception as e:
            logger.error(f"LSTM forecasting error: {e}")
            # Fallback to simple linear regression
            return await self._linear_fallback(data, horizon)

    async def _linear_fallback(self, data: List[TimeSeriesData], horizon: int) -> Dict:
        """Simple linear regression fallback"""
        values = [d.value for d in data]
        x = np.arange(len(values))
        y = np.array(values)

        # Fit linear model
        coeffs = np.polyfit(x, y, 1)
        slope, intercept = coeffs

        # Predict
        future_x = np.arange(len(values), len(values) + horizon)
        predictions = slope * future_x + intercept

        return {
            "forecast": [
                {
                    "date": (data[-1].timestamp + timedelta(days=i+1)).isoformat(),
                    "predicted_value": float(pred),
                    "model": "linear_fallback"
                }
                for i, pred in enumerate(predictions)
            ],
            "model": "linear"
        }

class RiskAnalysisService:
    """Risk assessment and scoring"""

    async def calculate_risk_score(self, historical_data: List[TimeSeriesData]) -> float:
        """Calculate risk score based on volatility"""
        values = [d.value for d in historical_data]

        # Calculate volatility (standard deviation of returns)
        returns = np.diff(values) / values[:-1]
        volatility = np.std(returns) if len(returns) > 0 else 0

        # Normalize to 0-100 scale
        risk_score = min(volatility * 100, 100)
        return risk_score

    async def detect_trend(self, historical_data: List[TimeSeriesData]) -> str:
        """Detect overall trend"""
        values = [d.value for d in historical_data]

        if len(values) < 2:
            return "neutral"

        # Simple moving average crossover
        short_ma = np.mean(values[-5:]) if len(values) >= 5 else values[-1]
        long_ma = np.mean(values[-20:]) if len(values) >= 20 else np.mean(values)

        if short_ma > long_ma * 1.02:  # 2% threshold
            return "bullish"
        elif short_ma < long_ma * 0.98:
            return "bearish"
        else:
            return "neutral"

class ClaudeAnalysisService:
    """Financial analysis using Claude AI"""

    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    async def analyze_forecast(
        self,
        security_id: str,
        historical_data: List[TimeSeriesData],
        forecast: List[Dict],
        trend: str,
        risk_score: float
    ) -> Dict[str, Any]:
        """Deep financial analysis"""

        recent_prices = [d.value for d in historical_data[-30:]]
        forecast_prices = [f['predicted_value'] for f in forecast]

        prompt = f"""Analyze this financial forecast for {security_id}:

HISTORICAL PERFORMANCE (last 30 days):
- Starting price: ${recent_prices[0]:.2f}
- Current price: ${recent_prices[-1]:.2f}
- Change: {((recent_prices[-1] - recent_prices[0]) / recent_prices[0] * 100):.2f}%
- Volatility: {np.std(recent_prices):.2f}

FORECAST (next 30 days):
- Predicted price: ${forecast_prices[-1]:.2f}
- Expected change: {((forecast_prices[-1] - recent_prices[-1]) / recent_prices[-1] * 100):.2f}%
- Trend: {trend}
- Risk Score: {risk_score:.1f}/100

Provide investment analysis in JSON:
{{
  "market_sentiment": "bullish" | "bearish" | "neutral",
  "confidence_level": "high" | "medium" | "low",
  "key_factors": ["factor1", "factor2", ...],
  "recommendations": ["action1", "action2", ...],
  "risk_assessment": "...",
  "investment_horizon": "short-term" | "medium-term" | "long-term"
}}
"""

        try:
            response = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            import json
            analysis = json.loads(response.content[0].text)
            return analysis

        except Exception as e:
            logger.error(f"Claude analysis error: {e}")
            return {
                "market_sentiment": trend,
                "confidence_level": "medium",
                "key_factors": ["Historical trend", f"Risk score: {risk_score:.1f}"],
                "recommendations": ["Consult with financial advisor"],
                "risk_assessment": f"Risk score of {risk_score:.1f}/100",
                "investment_horizon": "medium-term"
            }

# ============================================================================
# APPLICATION
# ============================================================================

app = FastAPI(
    title="Financial Forecaster AI Agent",
    description="Time-series prediction, risk modeling, and portfolio optimization",
    version=config.VERSION
)

forecasting_service = ForecastingService()
risk_service = RiskAnalysisService()
claude_service = ClaudeAnalysisService(config.CLAUDE_API_KEY)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": config.VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/forecast", response_model=ForecastResponse)
async def create_forecast(request: ForecastRequest):
    """Generate financial forecast"""
    start_time = datetime.utcnow()
    forecast_counter.labels(type="forecast").inc()

    try:
        # Generate forecast using Prophet
        with forecast_duration.time():
            forecast_result = await forecasting_service.forecast_prophet(
                request.historical_data,
                request.forecast_horizon_days
            )

        # Risk analysis
        risk_score = await risk_service.calculate_risk_score(request.historical_data)
        trend = await risk_service.detect_trend(request.historical_data)

        # Claude analysis (if requested)
        claude_analysis = None
        recommendations = []

        if request.include_analysis:
            analysis = await claude_service.analyze_forecast(
                request.security_id,
                request.historical_data,
                forecast_result['forecast'],
                trend,
                risk_score
            )
            claude_analysis = analysis.get('risk_assessment', '')
            recommendations = analysis.get('recommendations', [])
        else:
            recommendations = [
                f"Trend: {trend}",
                f"Risk level: {'High' if risk_score > 60 else 'Medium' if risk_score > 30 else 'Low'}",
                "Consider diversification"
            ]

        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        return ForecastResponse(
            security_id=request.security_id,
            forecast=forecast_result['forecast'],
            confidence_intervals=[
                {
                    "date": f['date'],
                    "lower": f.get('lower_bound', f['predicted_value'] * 0.95),
                    "upper": f.get('upper_bound', f['predicted_value'] * 1.05)
                }
                for f in forecast_result['forecast']
            ],
            trend=trend,
            risk_score=risk_score,
            claude_analysis=claude_analysis,
            recommendations=recommendations,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Forecast failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")

@app.get("/")
async def root():
    return {
        "service": "Financial Forecaster AI Agent",
        "version": config.VERSION,
        "status": "operational",
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=config.PORT, workers=4, log_level="info")
