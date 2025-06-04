# t:\Work\xml_input_ui\tests\test_command_manager.py
import unittest
from unittest.mock import MagicMock
from command_manager import CommandManager
from commands import Command # Import the base Command class for mocking

# Simple mock command for testing
class MockCommand(Command):
    def __init__(self, description="Mock Command"):
        super().__init__(description)
        self.executed = False
        self.unexecuted = False

    def execute(self):
        self.executed = True
        self.unexecuted = False # Reset unexecuted state on execute

    def unexecute(self):
        self.unexecuted = True
        self.executed = False # Reset executed state on unexecute

class TestCommandManager(unittest.TestCase):
    def setUp(self):
        # Mock the editor with the methods CommandManager calls
        self.mock_editor = MagicMock()
        self.mock_editor._log_history = MagicMock()
        self.mock_editor._set_dirty_flag = MagicMock()
        self.mock_editor._update_undo_redo_actions_state = MagicMock()

        self.command_manager = CommandManager(self.mock_editor)

    def test_initial_state(self):
        self.assertEqual(len(self.command_manager.undo_stack), 0)
        self.assertEqual(len(self.command_manager.redo_stack), 0)
        self.assertFalse(self.command_manager.can_undo())
        self.assertFalse(self.command_manager.can_redo()) # Should be False initially
        # _update_undo_redo_actions_state is called by clear_stacks, which is often
        # called during editor initialization, but not by CommandManager's __init__ itself.
        self.mock_editor._update_undo_redo_actions_state.assert_not_called()

    def test_execute_command(self):
        command1 = MockCommand("Cmd 1")
        command2 = MockCommand("Cmd 2")

        executed_cmd1 = self.command_manager.execute_command(command1)
        self.assertTrue(command1.executed)
        self.assertEqual(len(self.command_manager.undo_stack), 1)
        self.assertEqual(self.command_manager.undo_stack[-1], command1)
        self.assertEqual(len(self.command_manager.redo_stack), 0)
        self.assertTrue(self.command_manager.can_undo())
        self.assertFalse(self.command_manager.can_redo())
        self.mock_editor._log_history.assert_called_once_with("Executed: Cmd 1")
        self.mock_editor._set_dirty_flag.assert_called_once_with(True)
        self.mock_editor._update_undo_redo_actions_state.assert_called_once()
        self.assertEqual(executed_cmd1, command1) # Check return value

        self.mock_editor._log_history.reset_mock()
        self.mock_editor._set_dirty_flag.reset_mock()
        self.mock_editor._update_undo_redo_actions_state.reset_mock()

        executed_cmd2 = self.command_manager.execute_command(command2)
        self.assertTrue(command2.executed)
        self.assertEqual(len(self.command_manager.undo_stack), 2)
        self.assertEqual(self.command_manager.undo_stack[-1], command2)
        self.assertEqual(len(self.command_manager.redo_stack), 0) # Redo stack cleared
        self.assertTrue(self.command_manager.can_undo())
        self.assertFalse(self.command_manager.can_redo())
        self.mock_editor._log_history.assert_called_once_with("Executed: Cmd 2")
        self.mock_editor._set_dirty_flag.assert_called_once_with(True)
        self.mock_editor._update_undo_redo_actions_state.assert_called_once()
        self.assertEqual(executed_cmd2, command2)

    def test_undo_redo_cycle(self):
        command1 = MockCommand("Cmd 1")
        command2 = MockCommand("Cmd 2")

        self.command_manager.execute_command(command1)
        self.command_manager.execute_command(command2)
        self.assertEqual(len(self.command_manager.undo_stack), 2)
        self.assertEqual(len(self.command_manager.redo_stack), 0)
        self.assertTrue(self.command_manager.can_undo())
        self.assertFalse(self.command_manager.can_redo())
        self.mock_editor._log_history.reset_mock()
        self.mock_editor._set_dirty_flag.reset_mock()
        self.mock_editor._update_undo_redo_actions_state.reset_mock() # Reset after executes

        # Undo command2
        undone_cmd = self.command_manager.undo()
        self.assertTrue(command2.unexecuted)
        self.assertEqual(len(self.command_manager.undo_stack), 1)
        self.assertEqual(self.command_manager.undo_stack[-1], command1)
        self.assertEqual(len(self.command_manager.redo_stack), 1)
        self.assertEqual(self.command_manager.redo_stack[-1], command2)
        self.assertTrue(self.command_manager.can_undo())
        self.assertTrue(self.command_manager.can_redo())
        self.mock_editor._log_history.assert_called_once_with("Undone: Cmd 2")
        self.mock_editor._set_dirty_flag.assert_called_once_with(True)
        self.mock_editor._update_undo_redo_actions_state.assert_called_once()
        self.assertEqual(undone_cmd, command2) # Check return value

        self.mock_editor._log_history.reset_mock()
        self.mock_editor._set_dirty_flag.reset_mock()
        self.mock_editor._update_undo_redo_actions_state.reset_mock()

        # Undo command1
        undone_cmd = self.command_manager.undo()
        self.assertTrue(command1.unexecuted)
        self.assertEqual(len(self.command_manager.undo_stack), 0)
        self.assertEqual(len(self.command_manager.redo_stack), 2)
        self.assertEqual(self.command_manager.redo_stack[-1], command1)
        self.assertFalse(self.command_manager.can_undo())
        self.assertTrue(self.command_manager.can_redo())
        self.mock_editor._log_history.assert_called_once_with("Undone: Cmd 1")
        self.mock_editor._set_dirty_flag.assert_called_once_with(True)
        self.mock_editor._update_undo_redo_actions_state.assert_called_once()
        self.assertEqual(undone_cmd, command1) # Check return value

        self.mock_editor._log_history.reset_mock()
        self.mock_editor._set_dirty_flag.reset_mock()
        self.mock_editor._update_undo_redo_actions_state.reset_mock()

        # Redo command1
        redone_cmd = self.command_manager.redo()
        self.assertTrue(command1.executed) # Should be executed again
        self.assertEqual(len(self.command_manager.undo_stack), 1)
        self.assertEqual(self.command_manager.undo_stack[-1], command1)
        self.assertEqual(len(self.command_manager.redo_stack), 1)
        self.assertEqual(self.command_manager.redo_stack[-1], command2)
        self.assertTrue(self.command_manager.can_undo())
        self.assertTrue(self.command_manager.can_redo())
        self.mock_editor._log_history.assert_called_once_with("Redone: Cmd 1")
        self.mock_editor._set_dirty_flag.assert_called_once_with(True)
        self.mock_editor._update_undo_redo_actions_state.assert_called_once()
        self.assertEqual(redone_cmd, command1) # Check return value

        self.mock_editor._log_history.reset_mock()
        self.mock_editor._set_dirty_flag.reset_mock()
        self.mock_editor._update_undo_redo_actions_state.reset_mock()

        # Redo command2
        redone_cmd = self.command_manager.redo()
        self.assertTrue(command2.executed) # Should be executed again
        self.assertEqual(len(self.command_manager.undo_stack), 2)
        self.assertEqual(self.command_manager.undo_stack[-1], command2)
        self.assertEqual(len(self.command_manager.redo_stack), 0)
        self.assertTrue(self.command_manager.can_undo())
        self.assertFalse(self.command_manager.can_redo())
        self.mock_editor._log_history.assert_called_once_with("Redone: Cmd 2")
        self.mock_editor._set_dirty_flag.assert_called_once_with(True)
        self.mock_editor._update_undo_redo_actions_state.assert_called_once()
        self.assertEqual(redone_cmd, command2) # Check return value


    def test_undo_empty_stack(self):
        self.assertIsNone(self.command_manager.undo())
        self.mock_editor._log_history.assert_not_called()
        self.mock_editor._set_dirty_flag.assert_not_called()
        # _update_undo_redo_actions_state is called on init, but not again for failed undo
        self.mock_editor._update_undo_redo_actions_state.assert_not_called() # Not called for failed undo

    def test_redo_empty_stack(self):
        self.assertIsNone(self.command_manager.redo())
        self.mock_editor._log_history.assert_not_called()
        self.mock_editor._set_dirty_flag.assert_not_called()
        # _update_undo_redo_actions_state is called on init, but not again for failed redo
        self.mock_editor._update_undo_redo_actions_state.assert_not_called() # Not called for failed redo

    def test_clear_stacks(self):
        command1 = MockCommand("Cmd 1")
        command2 = MockCommand("Cmd 2")

        self.command_manager.execute_command(command1)
        self.command_manager.execute_command(command2)
        self.command_manager.undo() # Move one to redo stack

        self.assertEqual(len(self.command_manager.undo_stack), 1)
        self.assertEqual(len(self.command_manager.redo_stack), 1)
        self.assertTrue(self.command_manager.can_undo())
        self.assertTrue(self.command_manager.can_redo())

        self.mock_editor._update_undo_redo_actions_state.reset_mock() # Reset call count before clear

        self.command_manager.clear_stacks()

        self.assertEqual(len(self.command_manager.undo_stack), 0)
        self.assertEqual(len(self.command_manager.redo_stack), 0)
        self.assertFalse(self.command_manager.can_undo())
        self.assertFalse(self.command_manager.can_redo())
        self.mock_editor._update_undo_redo_actions_state.assert_called_once() # Called by clear_stacks

    def test_clear_stacks_no_editor(self):
        # Test that clear_stacks doesn't crash if editor is None
        cm_no_editor = CommandManager(None)
        command1 = MockCommand("Cmd 1")
        cm_no_editor.execute_command(command1) # Need to populate stacks
        cm_no_editor.undo() # Move to redo stack

        self.assertEqual(len(cm_no_editor.undo_stack), 0)
        self.assertEqual(len(cm_no_editor.redo_stack), 1)
        self.assertTrue(cm_no_editor.can_redo())

        cm_no_editor.clear_stacks()
        self.assertFalse(cm_no_editor.can_undo())
        self.assertFalse(cm_no_editor.can_redo())
        # Assert that no methods on a None editor were called
        # (This is implicitly tested by the lack of AttributeErrors)
