import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from services.orchestration_engine.orchestration_engine.workflow_manager import WorkflowManager

class TestWorkflowManager(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.agent_manager = MagicMock()
        self.analytics_manager = MagicMock()
        self.logger = MagicMock()
        self.workflow_manager = WorkflowManager(
            agent_manager=self.agent_manager,
            analytics_manager=self.analytics_manager,
            logger=self.logger
        )

    @patch('services.orchestration_engine.orchestration_engine.workflow_manager.get_db')
    async def test_create_and_dispatch_workflow(self, mock_get_db):
        # Setup mock DB session
        mock_session = AsyncMock()
        mock_get_db.return_value.__aiter__.return_value = [mock_session]
        
        # Setup mock Celery task
        with patch('services.orchestration_engine.orchestration_engine.workflow_manager.execute_workflow_task') as mock_task:
            workflow_id = await self.workflow_manager.create_and_dispatch_workflow(
                name="Test Workflow",
                tasks=[{"agent_id": "a1", "task_details": {}}],
                user_id=1
            )
            
            self.assertIsNotNone(workflow_id)
            mock_session.add.assert_called_once()
            mock_session.commit.assert_awaited_once()
            mock_task.delay.assert_called_once_with(workflow_id)

if __name__ == '__main__':
    unittest.main()
