import re
import os
import inspect
import importlib


def count_leading_spaces(s):
    ws = re.search(r"\S", s)
    if ws:
        return ws.start()
    else:
        return 0


def insert_in_file(markdown_text, file_path, tag):
    """Save module page.

    Either insert content into existing page,
    or create page otherwise."""
    replace_final_tag = False
    if file_path.exists():
        template = file_path.read_text(encoding="utf-8")
        if tag in template:
            markdown_text = template.replace(tag, markdown_text)
            print(("...inserting autogenerated content "
                   "for tag {0} into template:").format(tag), file_path)
        elif "{{autogenerated}}" in template:
            markdown_text = template.replace(
                "{{autogenerated}}", markdown_text + "{{autogenerated}}")
            print(("...appending autogenerated content "
                  "for {0} to template:").format(tag), file_path)
            replace_final_tag = True
        else:
            raise RuntimeError(("Template found for {0} but missing "
                                "{{{{autogenerated}}}} or {1} tag.").format(file_path, tag))
    else:
        print("...creating new page with autogenerated content:", file_path)
    os.makedirs(file_path.parent, exist_ok=True)
    file_path.write_text(markdown_text, encoding="utf-8")
    return replace_final_tag


def code_snippet(snippet):
    return f'```python\n{snippet}\n```\n'


def make_source_link(cls, project_url):
    if isinstance(project_url, dict):
        base_module = cls.__module__.split('.')[0]
        project_url = project_url[base_module]
    path = cls.__module__.replace(".", "/")
    line = inspect.getsourcelines(cls)[-1]
    return (f'<span style="float:right;">'
            f'[[source]]({project_url}/{path}.py#L{line})'
            f'</span>')


def format_classes_list(classes, page_name):
    for i in range(len(classes)):
        if not isinstance(classes[i], (list, tuple)):
            classes[i] = (classes[i], [])
    for class_, class_methods in classes:
        if not inspect.isclass(class_):
            # TODO: add a test for this
            raise TypeError(f'{class_} was given in the class list '
                            f'of {page_name} but {class_} is not a Python class.')
    return classes


def get_class_from_method(meth):
    """See
    https://stackoverflow.com/questions/3589311/
    get-defining-class-of-unbound-method-object-in-python-3/
    25959545#25959545
    """
    if inspect.ismethod(meth):
        for cls in inspect.getmro(meth.__self__.__class__):
            if cls.__dict__.get(meth.__name__) is meth:
                return cls
        meth = meth.__func__  # fallback to __qualname__ parsing
    if inspect.isfunction(meth):
        cls = getattr(inspect.getmodule(meth),
                      meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0])
        if isinstance(cls, type):
            return cls
    return getattr(meth, '__objclass__', None)  # handle special descriptor objects


def ismethod(function):
    return get_class_from_method(function) is not None


def import_object(string: str):
    """Import an object from a string.

    The object can be a function, class or method.
    For example: `'keras.layers.Dense.get_weights'` is valid.
    """
    last_object_got = None
    seen_names = []
    for name in string.split('.'):
        seen_names.append(name)
        try:
            last_object_got = importlib.import_module('.'.join(seen_names))
        except ModuleNotFoundError:
            last_object_got = getattr(last_object_got, name)
    return last_object_got


def get_type(object_) -> str:
    if inspect.isclass(object_):
        return 'class'
    elif ismethod(object_):
        return 'method'
    elif inspect.isfunction(object_):
        return 'function'
    else:
        raise TypeError(f'{object_} is detected as neither a class, a method nor'
                        f'a function.')


def insert_in_string(target, string_to_insert, start, end):
    target_start_cut = target[:start]
    target_end_cut = target[end:]
    return target_start_cut + string_to_insert + target_end_cut


def remove_indentation(string):
    string = string.replace('\n    ', '\n')
    if string[:4] == '    ':
        string = string[4:]
    return string


def get_dotted_path(class_):
    return f'{class_.__module__}.{class_.__qualname__}'
