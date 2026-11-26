"""Shared Spanish/English catalogue; language changes never touch exposure state."""
import json,re,string
from pathlib import Path
from PySide6.QtCore import QObject,Signal

class Language(QObject):
    changed=Signal()
    code='es'
language=Language()
CATALOG=json.loads(Path(__file__).with_name('translations.json').read_text(encoding='utf8'))
patterns=[]
for source,target in CATALOG.items():
    if '{' not in source:continue
    regex='';fields=[]
    for literal,name,spec,conversion in string.Formatter().parse(source):
        regex+=re.escape(literal)
        if name is not None:fields.append(name);regex+='(.+?)'
    patterns.append((re.compile('^'+regex+'$',re.S),fields,target))

def text(source):
    if language.code=='es' or not source:return source
    if source in CATALOG:return CATALOG[source]
    for regex,fields,target in patterns:
        match=regex.fullmatch(source)
        if match:return target.format(**dict(zip(fields,match.groups())))
    # Metadata joins invariant numeric parameters and a translated light name.
    for es in ('Día','Atardecer','Noche'):
        if source.endswith(' · '+es):return source[:-len(es)]+CATALOG[es]
    return source

def set_language(code):
    if code not in ('es','en'):raise ValueError('Unsupported language')
    if language.code!=code:language.code=code;language.changed.emit()

def canonical(value):
    for source,target in CATALOG.items():
        if value==target:return source
    for source,target in CATALOG.items():
        if '{' not in target:continue
        regex='';fields=[]
        for literal,name,spec,conversion in string.Formatter().parse(target):
            regex+=re.escape(literal)
            if name is not None:fields.append(name);regex+='(.+?)'
        match=re.fullmatch(regex,value,re.S)
        if match:return source.format(**dict(zip(fields,match.groups())))
    return value

class Translatable:
    def _bind_language(self):
        self._source_text=canonical(self.text());self._source_tooltip=canonical(self.toolTip());self._source_accessible=canonical(self.accessibleName())
        language.changed.connect(self._retranslate);self._retranslate()
    def _retranslate(self):
        super().setText(text(self._source_text));super().setToolTip(text(self._source_tooltip));super().setAccessibleName(text(self._source_accessible))
    def setText(self,value):
        self._source_text=canonical(value);super().setText(text(self._source_text))
    def setToolTip(self,value):
        self._source_tooltip=canonical(value);super().setToolTip(text(self._source_tooltip))
    def setAccessibleName(self,value):
        self._source_accessible=canonical(value);super().setAccessibleName(text(self._source_accessible))
