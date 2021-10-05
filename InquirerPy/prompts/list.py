"""Module contains the class to create a list prompt."""
import shutil
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from prompt_toolkit.application.application import Application
from prompt_toolkit.filters.cli import IsDone
from prompt_toolkit.layout.containers import (
    ConditionalContainer,
    Float,
    FloatContainer,
    HSplit,
    Window,
)
from prompt_toolkit.layout.controls import DummyControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.validation import ValidationError
from prompt_toolkit.widgets.base import Frame

from InquirerPy.base import InquirerPyUIListControl
from InquirerPy.base.complex import FakeDocument
from InquirerPy.base.list import BaseListPrompt
from InquirerPy.containers.instruction import InstructionWindow
from InquirerPy.containers.message import MessageWindow
from InquirerPy.containers.validation import ValidationWindow
from InquirerPy.enum import INQUIRERPY_POINTER_SEQUENCE
from InquirerPy.separator import Separator
from InquirerPy.utils import (
    InquirerPyDefault,
    InquirerPyListChoices,
    InquirerPyMessage,
    InquirerPySessionResult,
    InquirerPyStyle,
    InquirerPyValidate,
    calculate_height,
)

__all__ = ["ListPrompt"]


class InquirerPyListControl(InquirerPyUIListControl):
    """An :class:`~prompt_toolkit.layout.UIControl` class that displays a list of choices.

    Reference the parameter definition in :class:`.ListPrompt`.
    """

    def __init__(
        self,
        choices: InquirerPyListChoices,
        default: Any,
        pointer: str,
        marker: str,
        session_result: Optional[InquirerPySessionResult],
        multiselect: bool,
        marker_pl: str,
    ) -> None:
        self._pointer: str = pointer
        self._marker: str = marker
        self._marker_pl: str = marker_pl
        super().__init__(
            choices=choices,
            default=default,
            session_result=session_result,
            multiselect=multiselect,
        )

    def _get_hover_text(self, choice) -> List[Tuple[str, str]]:
        display_choices = []
        display_choices.append(("class:pointer", self._pointer))
        display_choices.append(
            (
                "class:marker",
                self._marker if choice["enabled"] else self._marker_pl,
            )
        )
        display_choices.append(("[SetCursorPosition]", ""))
        display_choices.append(("class:pointer", choice["name"]))
        return display_choices

    def _get_normal_text(self, choice) -> List[Tuple[str, str]]:
        display_choices = []
        display_choices.append(("", len(self._pointer) * " "))
        display_choices.append(
            (
                "class:marker",
                self._marker if choice["enabled"] else self._marker_pl,
            )
        )
        if not isinstance(choice["value"], Separator):
            display_choices.append(("", choice["name"]))
        else:
            display_choices.append(("class:separator", choice["name"]))
        return display_choices


class ListPrompt(BaseListPrompt):
    """Create a prompt that displays a list of choices to select.

    A wrapper class around :class:`~prompt_toolkit.application.Application`.

    Args:
        message: The question to ask the user.
            Refer to :ref:`pages/dynamic:message` documentation for more details.
        choices: List of choices to display and select.
            Refer to :ref:`pages/dynamic:choices` documentation for more details.
        style: An :class:`InquirerPyStyle` instance.
            Refer to :ref:`Style <pages/style:Alternate Syntax>` documentation for more details.
        vi_mode: Use vim keybinding for the prompt.
            Refer to :ref:`pages/kb:Keybindings` documentation for more details.
        default: Set the default value of the prompt.
            This will be used to determine which choice is highlighted (current selection),
            The default value should be the value of one of the choices.
            Refer to :ref:`pages/dynamic:default` documentation for more details.
        qmark: Question mark symbol. Custom symbol that will be displayed infront of the question before its answered.
        amark: Answer mark symbol. Custom symbol that will be displayed infront of the question after its answered.
        pointer: Pointer symbol. Customer symbol that will be used to indicate the current choice selection.
        instruction: Short instruction to display next to the question.
        long_instruction: Long instructions to display at the bottom of the prompt.
        validate: Add validation to user input.
            The main use case for this prompt would be when `multiselect` is True, you can enforce a min/max selection.
            Refer to :ref:`pages/validator:Validator` documentation for more details.
        invalid_message: Error message to display when user input is invalid.
            Refer to :ref:`pages/validator:Validator` documentation for more details.
        transformer: A function which performs additional transformation on the value that gets printed to the terminal.
            Different than `filter` parameter, this is only visual effect and won’t affect the actual value returned by :meth:`~InquirerPy.base.simple.BaseSimplePrompt.execute`.
            Refer to :ref:`pages/dynamic:transformer` documentation for more details.
        filter: A function which performs additional transformation on the result.
            This affects the actual value returned by :meth:`~InquirerPy.base.simple.BaseSimplePrompt.execute`.
            Refer to :ref:`pages/dynamic:filter` documentation for more details.
        height: Preferred height of the prompt.
            Refer to :ref:`pages/height:Height` documentation for more details.
        max_height: Max height of the prompt.
            Refer to :ref:`pages/height:Height` documentation for more details.
        multiselect: Enable multi-selection on choices.
            You can use `validate` parameter to control min/max selections.
            Setting to True will also change the result from a single value to a list of values.
        marker: Marker Symbol. Custom symbol to indicate if a choice is selected.
            This will take effects when `multiselect` is True.
        marker_pl: Marker place holder when the choice is not selected.
            This is empty space by default.
        border: Create border around the choice window.
        keybindings: Customise the builtin keybindings.
            Refer to :ref:`pages/kb:Keybindings` for more details.
        show_cursor: Display cursor at the end of the prompt.
            Set to False to hide the cursor.
        cycle: Return to top item if hit bottom during navigation or vice versa.
        wrap_lines: Soft wrap question lines when question exceeds the terminal width.
        session_result: Used internally for :ref:`index:Classic Syntax (PyInquirer)`.

    Examples:
        >>> from InquirerPy import inquirer
        >>> result = inquirer.select(message="Select one:", choices=[1, 2, 3]).execute()
        >>> print(result)
        1
    """

    def __init__(
        self,
        message: InquirerPyMessage,
        choices: InquirerPyListChoices,
        default: InquirerPyDefault = None,
        style: InquirerPyStyle = None,
        vi_mode: bool = False,
        qmark: str = "?",
        amark: str = "?",
        pointer: str = INQUIRERPY_POINTER_SEQUENCE,
        instruction: str = "",
        long_instruction: str = "",
        transformer: Callable[[Any], Any] = None,
        filter: Callable[[Any], Any] = None,
        height: Union[int, str] = None,
        max_height: Union[int, str] = None,
        multiselect: bool = False,
        marker: str = INQUIRERPY_POINTER_SEQUENCE,
        marker_pl: str = " ",
        border: bool = False,
        validate: InquirerPyValidate = None,
        invalid_message: str = "Invalid input",
        keybindings: Dict[str, List[Dict[str, Any]]] = None,
        show_cursor: bool = True,
        cycle: bool = True,
        wrap_lines: bool = True,
        spinner_enable: bool = False,
        spinner_pattern: List[str] = None,
        spinner_text: str = "",
        spinner_delay: float = 0.1,
        set_exception_handler: bool = True,
        session_result: InquirerPySessionResult = None,
    ) -> None:
        if not hasattr(self, "_content_control"):
            self.content_control = InquirerPyListControl(
                choices=choices,
                default=default,
                pointer=pointer,
                marker=marker,
                session_result=session_result,
                multiselect=multiselect,
                marker_pl=marker_pl,
            )
        super().__init__(
            message=message,
            style=style,
            border=border,
            vi_mode=vi_mode,
            qmark=qmark,
            amark=amark,
            instruction=instruction,
            long_instruction=long_instruction,
            transformer=transformer,
            filter=filter,
            validate=validate,
            invalid_message=invalid_message,
            multiselect=multiselect,
            keybindings=keybindings,
            cycle=cycle,
            wrap_lines=wrap_lines,
            spinner_enable=spinner_enable,
            spinner_pattern=spinner_pattern,
            spinner_delay=spinner_delay,
            spinner_text=spinner_text,
            set_exception_handler=set_exception_handler,
            session_result=session_result,
        )
        self._show_cursor = show_cursor
        self._dimmension_height, self._dimmension_max_height = calculate_height(
            height, max_height, height_offset=self.height_offset
        )
        main_content_window = Window(
            content=self.content_control,
            height=Dimension(
                max=self._dimmension_max_height,
                preferred=self._dimmension_height,
            ),
            dont_extend_height=True,
        )

        if self._border:
            main_content_window = Frame(main_content_window)

        self.layout = FloatContainer(
            content=HSplit(
                [
                    MessageWindow(
                        message=self._get_prompt_message_with_cursor
                        if self._show_cursor
                        else self._get_prompt_message,
                        filter=~self._is_loading | ~self._is_spinner_enable,
                        wrap_lines=self._wrap_lines,
                        show_cursor=self._show_cursor,
                    ),
                    self._spinner,
                    ConditionalContainer(
                        main_content_window,
                        filter=~IsDone() & ~self._is_loading,
                    ),
                    ConditionalContainer(
                        Window(content=DummyControl()),
                        filter=~IsDone() & self._is_displaying_long_instruction,
                    ),
                    InstructionWindow(
                        message=self._long_instruction,
                        filter=self._is_displaying_long_instruction & ~IsDone(),
                        wrap_lines=self._wrap_lines,
                    ),
                ]
            ),
            floats=[
                Float(
                    content=ValidationWindow(
                        invalid_message=self._get_error_message,
                        filter=self._is_invalid & ~IsDone(),
                    ),
                    left=0,
                    bottom=0,
                ),
            ],
        )

        self.application = Application(
            layout=Layout(self.layout),
            style=self._style,
            key_bindings=self._kb,
            after_render=self._after_render,
        )

    def _get_prompt_message_with_cursor(self) -> List[Tuple[str, str]]:
        """Obtain the prompt message to display and display cursor behind the message.

        This ensures that cursor is always at the end of the window.
        """
        message = self._get_prompt_message()
        message.append(("[SetCursorPosition]", ""))
        message.append(("", " "))  # [SetCursorPosition] require char behind it
        return message

    def _toggle_choice(self) -> None:
        """Toggle the `enabled` status of the choice."""
        self.content_control.selection["enabled"] = not self.content_control.selection[
            "enabled"
        ]

    def _toggle_all(self, value: bool = None) -> None:
        """Toggle all choice `enabled` status.

        Args:
            value: Sepcify a value to toggle.
        """
        for choice in self.content_control.choices:
            if isinstance(choice["value"], Separator):
                continue
            choice["enabled"] = value if value else not choice["enabled"]

    def _handle_up(self) -> None:
        """Handle the event when user attempt to move up."""
        while True:
            cap = super()._handle_up()
            if not isinstance(self.content_control.selection["value"], Separator):
                break
            else:
                if cap and not self._cycle:
                    self._handle_down()
                    break

    def _handle_down(self) -> None:
        """Handle the event when user attempt to move down."""
        while True:
            cap = super()._handle_down()
            if not isinstance(self.content_control.selection["value"], Separator):
                break
            else:
                if cap and not self._cycle:
                    self._handle_up()
                    break

    def _handle_enter(self, event) -> None:
        """Handle the event when user hit `enter` key.

        1. Set the prompt state to answered.
        2. Set the result to the name of the selected choices.
        3. Exit the app with the value of the selected choices.

        In multiselect scenario, if nothing is selected, return the current highlighted choice.
        """
        try:
            fake_document = FakeDocument(self.result_value)
            self._validator.validate(fake_document)  # type: ignore
        except ValidationError as e:
            self._set_error(str(e))
        else:
            self.status["answered"] = True
            if self._multiselect and not self.selected_choices:
                self.status["result"] = [self.content_control.selection["name"]]
                event.app.exit(result=[self.content_control.selection["value"]])
            else:
                self.status["result"] = self.result_name
                event.app.exit(result=self.result_value)

    @property
    def wrap_lines_offset(self) -> int:
        """Get extra offset due to line wrapping.

        Overriding it to count the cursor as well.

        Returns:
            Extra offset value.
        """
        if not self._wrap_lines:
            return 0
        total_message_length = self.total_message_length
        if self._show_cursor:
            total_message_length += 1
        term_width, _ = shutil.get_terminal_size()
        return total_message_length // term_width
