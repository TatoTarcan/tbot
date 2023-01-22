import collections.abc
import inspect
import re
import typing
from collections import defaultdict
from typing import Any, Iterator, Union

import telegram
import telegram.ext


class AdmonitionInserter:
    """Class for inserting admonitions into docs of Telegram classes."""

    ADMONITION_TYPES = ("use_in", "available_in", "returned_in")

    FORWARD_REF_PATTERN = re.compile(r"^ForwardRef\('(?P<class_name>\w+)'\)$")
    """ A pattern to find a class name in a ForwardRef typing annotation.
    Class name (in a named group) is surrounded by parentheses and single quotes.
    Note that since we're analyzing argument by argument, the pattern can be strict, with
    start and end markers.
    """

    METHODS_FOR_BOT_AND_APPBUILDER = {
        telegram.Bot: tuple(
            m[0]
            for m in inspect.getmembers(telegram.Bot, inspect.isfunction)  # not .ismethod
            if not m[0].startswith("_")
            and m[0].islower()  # islower() to avoid camelCase methods
            and m[0] in telegram.Bot.__dict__  # method is not inherited from TelegramObject
        ),
        telegram.ext.ApplicationBuilder: tuple(
            m[0]
            for m in inspect.getmembers(telegram.ext.ApplicationBuilder, inspect.isfunction)
            if not m[0].startswith("_") and m[0] in telegram.ext.ApplicationBuilder.__dict__
        ),
    }
    """Relevant methods to be mentioned in 'Returned in' and 'Use in' admonitions:
    Bot methods(public, not aliases, not inherited from TelegramObject) and ApplicationBuilder
    methods.
    """

    def __init__(self):
        self.admonitions: dict[str, dict[type, str]] = {
            # dynamically determine which method to use to create a sub-dictionary
            admonition_type: getattr(self, f"_create_{admonition_type}")()
            for admonition_type in self.ADMONITION_TYPES
        }
        """Dictionary with admonitions. Contains sub-dictionaries, one per admonition type.
        Each sub-dictionary matches classes to texts of admonitions, e.g.:
        ```
        {
        "use_in": {<class 'telegram._chatinvitelink.ChatInviteLink'>:
        <"Use in" admonition for ChatInviteLink>, ...},
        "available_in": {<class 'telegram._chatinvitelink.ChatInviteLink'>:
        <"Available in" admonition">, ...},
        "returned_in": {...}
        }
        ```
        """

    def insert_admonitions_for_class(
        self,
        cls: type,
        docstring_lines: list[str],
    ):
        """Inserts admonitions into docstring lines for a given class.

        **Modifies lines in place**.
        """
        # A better way would be to copy the lines and return them, but that will not work with
        # autodoc_process_docstring()

        for admonition_type in self.ADMONITION_TYPES:

            # If there is no admonition of the given type for the given class,
            # continue to the next admonition type, maybe the class is listed there.
            if cls not in self.admonitions[admonition_type]:
                continue

            insert_idx = self._find_insert_pos_for_admonition(docstring_lines)
            admonition_lines = self.admonitions[admonition_type][cls].splitlines()

            for idx in range(insert_idx, insert_idx + len(admonition_lines)):
                docstring_lines.insert(idx, admonition_lines[idx - insert_idx])

    def _create_available_in(self) -> dict[type, str]:
        """Creates a dictionary with 'Available in' admonitions for classes that are available
        in attributes of other classes.
        """

        # Generate a mapping of classes to ReST links to attributes in other classes that
        # correspond to instances of a given class
        # i.e. {telegram._files.sticker.Sticker: {":attr:`telegram.Message.sticker`", ...}}
        attrs_for_class = defaultdict(set)

        # The following regex is supposed to capture a class name in a line like this:
        # media (:obj:`str` | :class:`telegram.InputFile`): Audio file to send.
        #
        # Note that even if such typing description spans over multiple lines but each line ends
        # with a backslash (otherwise Sphinx will throw an error)
        # (e.g. EncryptedPassportElement.data), then Sphinx will combine these lines into a single
        # line automatically, and it will contain no backslash (only some extra many whitespaces
        # from the indentation).

        attr_docstr_pattern = re.compile(
            r"^\s*(?P<attr_name>[a-z_]+)"  # Any number of spaces, named group for attribute
            r"\s?\("  # Optional whitespace, opening parenthesis
            r".*"  # Any number of characters (that could denote a built-in type)
            r":class:`.+`"  # Marker of a classref, class name in backticks
            r".*\):"  # Any number of characters, closing parenthesis, colon.
            # The ^ colon above along with parenthesis is important because it makes sure that
            # the class is mentioned in the attribute description, not in free text.
            r".*$",  # Any number of characters, end of string (end of line)
            re.VERBOSE,
        )

        # for properties: there is no attr name in docstring.  Just check if there's a class name.
        prop_docst_pattern = re.compile(r":class:`.+`.*:")

        # pattern for iterating over potentially many class names in docstring for one attribute.
        # Tilde is optional (sometimes it is in the docstring, sometimes not).
        single_class_name_pattern = re.compile(r":class:`~?(?P<class_name>[\w.]*)`")

        classes_to_inspect = inspect.getmembers(telegram, inspect.isclass) + inspect.getmembers(
            telegram.ext, inspect.isclass
        )

        for class_name, inspected_class in classes_to_inspect:
            # We need to make "<class 'telegram._files.sticker.StickerSet'>" into
            # "telegram.StickerSet" because that's the way the classes are mentioned in
            # docstrings.
            # Check for potential presence of ".ext.", we will need to keep it.
            ext = ".ext" if ".ext." in str(inspected_class) else ""
            name_of_inspected_class_in_docstr = f"telegram{ext}.{class_name}"

            # Parsing part of the docstring with attributes (parsing of properties follows later)
            docstring_lines = inspect.getdoc(inspected_class).splitlines()
            lines_with_attrs = []
            for idx, line in enumerate(docstring_lines):
                if line.strip() == "Attributes:":
                    lines_with_attrs = docstring_lines[idx + 1 :]
                    break

            for line in lines_with_attrs:
                line_match = attr_docstr_pattern.match(line)
                if not line_match:
                    continue

                target_attr = line_match.group("attr_name")
                # a typing description of one attribute can contain multiple classes
                for match in single_class_name_pattern.finditer(line):
                    name_of_class_in_attr = match.group("class_name")

                    # Writing to dictionary: matching the class found in the docstring
                    # and its subclasses to the attribute of the class being inspected.
                    # The class in the attribute docstring (or its subclass) is the key,
                    # the attribute of the class currently being inspected is the value.
                    try:
                        self._resolve_arg_and_add_link(
                            arg=name_of_class_in_attr,
                            dict_of_methods_for_class=attrs_for_class,
                            link=f":attr:`{name_of_inspected_class_in_docstr}.{target_attr}`",
                        )
                    except NotImplementedError as e:
                        raise NotImplementedError(
                            f"Error generating Sphinx 'Available in' admonition "
                            f"(admonition_inserter.py). Class {name_of_class_in_attr} present in "
                            f"attribute {target_attr} of class {name_of_inspected_class_in_docstr}"
                            f" could not be resolved. {str(e)}"
                        )

            # Properties need to be parsed separately because they act like attributes but not
            # listed as attributes.
            properties = inspect.getmembers(inspected_class, lambda o: isinstance(o, property))
            for prop_name, _ in properties:
                # Make sure this property is really defined in the class being inspected.
                # A property can be inherited from a parent class, then a link to it will not work.
                if prop_name not in inspected_class.__dict__:
                    continue

                # 1. Can't use typing.get_type_hints because double-quoted type hints
                #    (like "Application") will throw a NameError
                # 2. Can't use inspect.signature because return annotations of properties can be
                #    hard to parse (like "(self) -> BD").
                # 3. fget is used to access the actual function under the property wrapper
                docstring = inspect.getdoc(getattr(inspected_class, prop_name).fget)
                if docstring is None:
                    continue

                first_line = docstring.splitlines()[0]
                if not prop_docst_pattern.match(first_line):
                    continue

                for match in single_class_name_pattern.finditer(first_line):
                    name_of_class_in_prop = match.group("class_name")

                    # Writing to dictionary: matching the class found in the docstring and its
                    # subclasses to the property of the class being inspected.
                    # The class in the property docstring (or its subclass) is the key,
                    # and the property of the class currently being inspected is the value.
                    try:
                        self._resolve_arg_and_add_link(
                            arg=name_of_class_in_prop,
                            dict_of_methods_for_class=attrs_for_class,
                            link=f":attr:`{name_of_inspected_class_in_docstr}.{prop_name}`",
                        )
                    except NotImplementedError as e:
                        raise NotImplementedError(
                            f"Error generating Sphinx 'Available in' admonition "
                            f"(admonition_inserter.py). Class {name_of_class_in_prop} present in "
                            f"property {prop_name} of class {name_of_inspected_class_in_docstr}"
                            f" could not be resolved. {str(e)}"
                        )

        return self._generate_admonitions(attrs_for_class, admonition_type="available_in")

    def _create_returned_in(self) -> dict[type, str]:
        """Creates a dictionary with 'Returned in' admonitions for classes that are returned
        in Bot's and ApplicationBuilder's methods.
        """

        # Generate a mapping of classes to ReST links to Bot methods which return it,
        # i.e. {<class 'telegram._message.Message'>: {:meth:`telegram.Bot.send_message`, ...}}
        methods_for_class = defaultdict(set)

        for cls, methods in self.METHODS_FOR_BOT_AND_APPBUILDER.items():
            for method in methods:

                sig = inspect.signature(getattr(cls, method))
                ret_annot = sig.return_annotation

                method_link = self._generate_link_to_method(method, cls)

                try:
                    self._resolve_arg_and_add_link(
                        arg=ret_annot,
                        dict_of_methods_for_class=methods_for_class,
                        link=method_link,
                    )
                except NotImplementedError as e:
                    raise NotImplementedError(
                        f"Error generating Sphinx 'Returned in' admonition "
                        f"(admonition_inserter.py). {cls}, method {method}. "
                        f"Couldn't resolve type hint in return annotation {ret_annot}. {str(e)}"
                    )

        return self._generate_admonitions(methods_for_class, admonition_type="returned_in")

    def _create_use_in(self) -> dict[type, str]:
        """Creates a dictionary with 'Use in' admonitions for classes whose instances are
        accepted as arguments for Bot's and ApplicationBuilder's methods.
        """

        # Generate a mapping of classes to links to Bot methods which accept them as arguments,
        # i.e. {<class 'telegram._inline.inlinequeryresult.InlineQueryResult'>:
        # {:meth:`telegram.Bot.answer_inline_query`, ...}}
        methods_for_class = defaultdict(set)  # using set because there can be repetitions

        for cls, relevant_methods_for_class in self.METHODS_FOR_BOT_AND_APPBUILDER.items():
            for method in relevant_methods_for_class:
                method_link = self._generate_link_to_method(method, cls)

                sig = inspect.signature(getattr(cls, method))
                parameters = sig.parameters

                for param in parameters.values():
                    try:
                        self._resolve_arg_and_add_link(
                            arg=param.annotation,
                            dict_of_methods_for_class=methods_for_class,
                            link=method_link,
                        )
                    except NotImplementedError as e:
                        raise NotImplementedError(
                            f"Error generating Sphinx 'Use in' admonition "
                            f"(admonition_inserter.py). {cls}, method {method}, parameter "
                            f"{param}: Couldn't resolve type hint {param.annotation}. {str(e)}"
                        )

        return self._generate_admonitions(methods_for_class, admonition_type="use_in")

    @staticmethod
    def _find_insert_pos_for_admonition(lines: list[str]) -> int:
        """Finds the correct position to insert the class admonition and returns the index.

        The admonition will be insert above "See also", "Examples:", version added/changed notes
        and args, whatever comes first.

        If no key phrases are found, the admonition will be inserted at the very end.
        """
        for idx, value in list(enumerate(lines)):
            if (
                value.startswith(".. seealso:")
                # The docstring contains heading "Examples:", but Sphinx will have it converted
                # to ".. admonition: Examples".
                or value.startswith(".. admonition:: Examples")
                or value.startswith(".. version")
                # The space after ":param" is important because docstring can contain ":paramref:"
                # in its plain text in the beginning of a line (e.g. ExtBot)
                or value.startswith(":param ")
                # some classes (like "Credentials") have no params, so insert before attrs:
                or value.startswith(".. attribute::")
            ):
                return idx
        return len(lines) - 1

    def _generate_admonitions(
        self,
        attrs_or_methods_for_class: dict[type, set[str]],
        admonition_type: str,
    ) -> dict[type, str]:
        """Generates admonitions of a given type.
        Takes a dictionary of classes matched to ReST links to methods or attributes, e.g.:

        ```
        {<class 'telegram._files.sticker.StickerSet'>:
        [":meth: `telegram.Bot.get_sticker_set`", ...]}.
        ```

        Returns a dictionary of class **names** matched to full admonitions, e.g.
        for `admonition_type` "returned_in" (note that title and CSS class are generated
        automatically):

        ```
        {"<class 'telegram._files.sticker.StickerSet'>":
        ".. admonition:: Returned in:
            :class: returned-in

            :meth: `telegram.Bot.get_sticker_set`"}.
        ```
        """

        if admonition_type not in self.ADMONITION_TYPES:
            raise TypeError(f"Admonition type {admonition_type} not supported.")

        admonition_for_class = {}

        for cls, attrs in attrs_or_methods_for_class.items():

            if cls is telegram.ext.ApplicationBuilder:
                # ApplicationBuilder is only used in and returned from its own methods,
                # so its page needs no admonitions.
                continue

            attrs = sorted(attrs)

            # for admonition type "use_in" the title will be "Use in" and CSS class "use-in".
            admonition = f"""

.. admonition:: {admonition_type.title().replace("_", " ")}
    :class: {admonition_type.replace("_", "-")}
    """
            if len(attrs) > 1:
                for target_attr in attrs:
                    admonition += "\n    * " + target_attr
            else:
                admonition += f"\n    {attrs[0]}"

            admonition += "\n    "  # otherwise an unexpected unindent warning will be issued
            admonition_for_class[cls] = admonition

        return admonition_for_class

    @staticmethod
    def _generate_link_to_method(method_name: str, base_class: type):
        """Generates a ReST link to a Bot method."""
        if base_class == telegram.Bot:
            return f":meth:`telegram.Bot.{method_name}`"
        elif base_class == telegram.ext.ApplicationBuilder:
            return f":meth:`telegram.ext.ApplicationBuilder.{method_name}`"
        else:
            raise NotImplementedError(f"Base class {base_class} not supported")

    @staticmethod
    def _iter_subclasses(cls: type) -> Iterator:
        return (
            # exclude private classes
            c
            for c in cls.__subclasses__()
            if not str(c).split(".")[-1].startswith("_")
        )

    def _resolve_arg_and_add_link(
        self,
        arg: Any,
        dict_of_methods_for_class: defaultdict,
        link: str,
    ) -> None:
        """A helper method. Tries to resolve the arg to a valid class. In case of success,
        adds the link (to a method, attribute, or property) for that class' and its subclasses'
        sets of links in the dictionary of admonitions.

        **Modifies dictionary in place.**
        """
        for cls in self._resolve_arg(arg):

            # When trying to resolve an argument from args or return annotation,
            # the method _resolve_arg returns None if nothing could be resolved.
            # Also, if class was resolved correctly, "telegram" will definitely be in its str().
            if cls is None or "telegram" not in str(cls):
                continue

            dict_of_methods_for_class[cls].add(link)

            for subclass in self._iter_subclasses(cls):
                dict_of_methods_for_class[subclass].add(link)

    def _resolve_arg(self, arg: Any) -> Iterator[Union[type, None]]:
        """Analyzes an argument of a method and recursively yields classes that the argument
        or its sub-arguments (in cases like Union[...]) belong to, if they can be resolved to
        telegram or telegram.ext classes.

        Raises `NotImplementedError`.
        """

        origin = typing.get_origin(arg)

        if (
            origin in (collections.abc.Callable, typing.IO)
            or arg is None
            # no other check available (by type or origin) for these:
            or str(type(arg)) in ("<class 'typing._SpecialForm'>", "<class 'ellipsis'>")
        ):
            pass

        # RECURSIVE CALLS
        # for cases like Union[Sequence....
        elif origin in (
            Union,
            collections.abc.Coroutine,
            collections.abc.Sequence,
        ):
            for sub_arg in typing.get_args(arg):
                yield from self._resolve_arg(sub_arg)

        elif isinstance(arg, typing.TypeVar):
            # gets access to the "bound=..." parameter
            yield from self._resolve_arg(arg.__bound__)
        # END RECURSIVE CALLS

        elif isinstance(arg, typing.ForwardRef):
            m = self.FORWARD_REF_PATTERN.match(str(arg))
            # We're sure it's a ForwardRef, so, unless it belongs to known exceptions,
            # the class must be resolved.
            # If it isn't resolved, we'll have the program throw an exception to be sure.
            try:
                cls = self._resolve_class(m.group("class_name"))
            except AttributeError:
                if str(arg) == "ForwardRef('DefaultValue[DVType]')":
                    # this is a known ForwardRef that needs not be resolved to a Telegram class
                    pass
                else:
                    raise NotImplementedError(f"Could not process ForwardRef: {arg}")
            else:
                yield cls

        elif isinstance(arg, type):
            if "telegram" in str(arg):
                yield arg

        # for custom generics like telegram.ext._application.Application[~BT, ~CCT, ~UD...]
        elif str(type(arg)) == "<class 'typing._GenericAlias'>":
            if "telegram" in str(arg):
                # get_origin() of telegram.ext._application.Application[~BT, ~CCT, ~UD...]
                # will produce <class 'telegram.ext._application.Application'>
                yield origin

        # For some reason "InlineQueryResult", "InputMedia" & some others are currently not
        # recognized as ForwardRefs and are identified as plain strings.
        elif isinstance(arg, str):

            # args like "ApplicationBuilder[BT, CCT, UD, CD, BD, JQ]" can be recognized as strings.
            # Remove whatever is in the square brackets because it doesn't need to be parsed.
            arg = re.sub(r"\[.+]", "", arg)

            cls = self._resolve_class(arg)
            # Here we don't want an exception to be thrown since we're not sure it's ForwardRef
            if cls is not None:
                yield cls

        else:
            raise NotImplementedError(
                f"Cannot process argument {arg} of type {type(arg)} (origin {origin})"
            )

    @staticmethod
    def _resolve_class(name: str) -> Union[type, None]:
        """The keys in the admonitions dictionary are not strings like "telegram.StickerSet"
        but classes like <class 'telegram._files.sticker.StickerSet'>.

        This method attempts to resolve a PTB class from a name that does or does not
        contain the word 'telegram', e.g.
        <class 'telegram._files.sticker.StickerSet'> from "telegram.StickerSet" or "StickerSet".

        Returns a class on success, :obj:`None` if nothing could be resolved.
        """

        for option in (
            name,
            f"telegram.{name}",
            f"telegram.ext.{name}",
            f"telegram.ext.filters.{name}",
        ):
            try:
                return eval(option)
            # NameError will be raised if trying to eval just name and it doesn't work, e.g.
            # "Name 'ApplicationBuilder' is not defined".
            # AttributeError will be raised if trying to e.g. eval f"telegram.{name}" when the
            # class denoted by `name` actually belongs to `telegram.ext`:
            # "module 'telegram' has no attribute 'ApplicationBuilder'".
            # If neither option works, this is not a PTB class.
            except (NameError, AttributeError):
                continue


if __name__ == "__main__":
    # just try instantiating for debugging purposes
    AdmonitionInserter()
