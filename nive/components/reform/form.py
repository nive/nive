import re

from nive.components.reform.widget import FormWidget
from nive.components.reform.field import Field
from nive.components.reform.schema import Schema

class Form(Field):
    """
    Field representing an entire form.

    Arguments:

    schema
        A :class:`colander.SchemaNode` object representing a
        schema to be rendered.  Required.

    action
        The form action (inserted into the ``action`` attribute of
        the form's form tag when rendered).  Default: the empty string.

    method
        The form method (inserted into the ``method`` attribute of
        the form's form tag when rendered).  Default: ``POST``. 

    buttons
        A sequence of strings or :class:`reform.form.Button`
        objects representing submit buttons that will be placed at
        the bottom of the form.  If any string is passed in the
        sequence, it is converted to
        :class:`reform.form.Button` objects.

    formid
        The identifier for this form.  This value will be used as the
        HTML ``id`` attribute of the rendered HTML form.  It will also
        be used as the value of a hidden form input control
        (``__formid__``) which will be placed in this form's
        rendering.  You should pass a string value for ``formid`` when
        more than one reform form is placed into a single page and
        both share the same action.  When one of the forms on the page
        is posted, your code will to be able to decide which of those
        forms was posted based on the differing values of
        ``__formid__``.  By default, ``formid`` is ``reform``.
    
    use_ajax
       If this option is ``True``, the form will use AJAX (actually
       AJAH); when any submit button is clicked, the DOM node related
       to this form will be replaced with the result of the form post
       caused by the submission.  The page will not be reloaded.  This
       feature uses the ``jquery.form`` library ``ajaxForm`` feature
       as per `http://jquery.malsup.com/form/
       <http://jquery.malsup.com/form/>`_.  Default: ``False``.  If
       this option is ``True``, the ``jquery.form.js`` library must be
       loaded in the HTML page which embeds the form.  A copy of it
       exists in the ``static`` directory of the ``reform`` package.

    ajax_options
       A *string* which must represent a JavaScript obejct
       (dictionary) of extra AJAX options as per
       `http://jquery.malsup.com/form/#options-object
       <http://jquery.malsup.com/form/#options-object>`_.  For
       example:

       .. code-block:: python

           '{"success": function (rText, sText, xhr, form) {alert(sText)};}'

       Default options exist even if ``ajax_options`` is not provided.
       By default, ``target`` points at the DOM node representing the
       form and and ``replaceTarget`` is ``true``. A successhandler calls
       the reform_ajaxify method that will ajaxify the newly written form
       again. the reform_ajaxify method is in the global namespace, it
       requires a oid, and accepts a method. If it receives a method,
       it will call the method after it ajaxified the form itself.
       If you pass these values in ``ajax_options``, the defaults will
       be overridden.
       If you want to override the success handler, don't forget to
       call the original reform_ajaxify successhandler, and pass your
       own method as an argument. Else, subsequent form submissions
       won't be submitted via AJAX.

       This option has no effect when ``use_ajax`` is False.

       The default value of ``ajax_options`` is a string
       representation of the empty object.

    The :class:`reform.Form` constructor also accepts all the keyword
    arguments accepted by the :class:`reform.Field` class.  These
    keywords mean the same thing in the context of a Form as they do
    in the context of a Field (a Form is just another kind of Field).
    """
    css_class = 'reform'
    view = None
    anchor = ''
    footer = ''
    uploadProgressBar = ''
    autofill = None

    
    def __init__(self, schema=None, action='', method='POST', buttons=(),
                 formid='reform', use_ajax=False, ajax_options='{}', **kw):
        if schema == None:
            schema = Schema()
        super(Form, self).__init__(schema, **kw)
        _buttons = []
        for button in buttons:
            if isinstance(button, str):
                button = Button(button)
            _buttons.append(button)
        self.action = action
        self.method = method
        self.buttons = _buttons
        self.formid = formid
        self.use_ajax = use_ajax
        self.ajax_options = Raw(ajax_options.strip())
        self.widget = FormWidget()


    def add(self, node, **kw):
        """
        Shortcut for Schema.add(). 'Directly adds the node to this forms schema.
        """
        self.schema.add(node)
        self.children.append(Field(node,
                                   renderer=self.renderer,
                                   counter=self.counter,
                                   resource_registry=self.resource_registry,
                                   **kw))


class Raw(str):
    def __html__(self):
        return self

class Button(object):
    """
    A class representing a form submit button.  A sequence of
    :class:`reform.widget.Button` objects may be passed to the
    constructor of a :class:`reform.form.Form` class when it is
    created to represent the buttons renderered at the bottom of the
    form.

    Arguments:

    name
        The string or unicode value used as the ``name`` of the button
        when rendered (the ``name`` attribute of the button or input
        tag resulting from a form rendering).  Default: ``submit``.

    title
        The value used as the title of the button when rendered (shows
        up in the button inner text).  Default: capitalization of
        whatever is passed as ``name``.  E.g. if ``name`` is passed as
        ``submit``, ``title`` will be ``Submit``.

    type
        The value used as the type of button. The HTML spec supports 
        ``submit``, ``reset`` and ``button``. Default: ``submit``. 

    value
        The value used as the value of the button when rendered (the
        ``value`` attribute of the button or input tag resulting from
        a form rendering).  Default: same as ``name`` passed.

    disabled
        Render the button as disabled if True.

    action
        The action this button represents.
        
    cls
        The css class used for this button as string.
    """
    def __init__(self, name='submit', title=None, type='submit', value=None,
                 disabled=False, action=None, cls=None):
        if title is None:
            title = name.capitalize()
        name = re.sub(r'\s', '_', name)
        if value is None:
            value = name
        self.name = name
        self.title = title
        self.type = type
        self.value = value
        self.disabled = disabled
        self.action = action
        self.cls = cls



class MemoryTmpStore(dict):
    """ Instances of this class implement the
    :class:`reform.interfaces.FileUploadTempStore` interface"""
    def preview_url(self, uid):
        return None

tmpstore = MemoryTmpStore()

