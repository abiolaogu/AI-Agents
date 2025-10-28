from setuptools import setup, find_packages

setup(
    name='competitor_analysis_agent',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'agent-framework @ file://localhost/./packages/agent_framework#egg=agent_framework',
    ],
)