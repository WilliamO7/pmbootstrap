import re


class ShellParser:
    REGEX_VARIABLE = re.compile(r"^([a-zA-Z0-9_]+)=(\"|)(.*?)(\"|)$")
    REGEX_NAME = re.compile(r"[a-zA-Z0-9_]")

    STATE_RAW = 0
    STATE_SUBST_COMPLEX = 1
    STATE_SUBST_SIMPLE = 2

    def __init__(self, data, environment=None):
        if hasattr(data, 'read'):
            with data:
                self.raw = data.read()
        else:
            self.raw = data
        self.variables = {}

        if environment is not None:
            self.variables.update(environment)

        self.parse()

    def parse(self):
        for line in self.raw.splitlines():
            variable = self.REGEX_VARIABLE.match(line)
            if variable is not None:
                name, startquote, value, endquote = variable.groups()
                if startquote == endquote:
                    result = self.process_substitutions(value)
                    self.variables[name] = result
                else:
                    # TODO: Implement multiline variables
                    pass

    def process_substitutions(self, value):
        value += "\0"
        state = self.STATE_RAW
        stack = []
        processed = ""
        simple = ""
        i = 0
        while i < len(value):
            char = value[i]
            if state == self.STATE_RAW:
                if char != "$":
                    processed += char
                else:
                    if value[i + 1] == "{":
                        state = self.STATE_SUBST_COMPLEX
                    else:
                        state = self.STATE_SUBST_SIMPLE

            elif state == self.STATE_SUBST_SIMPLE:
                if self.REGEX_NAME.match(char):
                    simple += char
                else:
                    processed += self.variables[simple]
                    simple = ""
                    state = self.STATE_RAW
                    i -= 1

            elif state == self.STATE_SUBST_COMPLEX:
                if char == "{":
                    stack.append("")
                elif char == "$" and value[i + 1] == "{":
                    stack.append("")
                    i += 1
                elif char == "}":
                    label = stack.pop()
                    label_value = self.process_substitution_value(label)
                    if len(stack) > 0:
                        stack[-1] += label_value
                    else:
                        processed += label_value
                        state = self.STATE_RAW

                else:
                    stack[-1] += char
            i += 1
        return processed[0:-1]

    def process_substitution_value(self, label):
        if label in self.variables:
            return self.variables[label]

        if ':-' in label:
            lookup, default = label.split(':')
            default = default[1:]
            if lookup in self.variables and self.variables[lookup] != "":
                return self.variables[lookup]
            else:
                return default

        if ':=' in label:
            lookup, default = label.split(':')
            default = default[1:]
            if lookup in self.variables and self.variables[lookup] != "":
                return self.variables[lookup]
            else:
                self.variables[lookup] = default
                return default

        if '=' in label:
            lookup, default = label.split('=')
            if lookup in self.variables:
                return self.variables[lookup]
            else:
                self.variables[lookup] = default
                return default

        if '#' in label:
            variable, pattern = label.split('#')
            if variable == "":
                return str(len(self.variables[pattern]))
            variable = self.variables[variable]
            if variable[0:len(pattern)] == pattern:
                return variable[len(pattern):]
            return variable

        raise KeyError("Could not find variable {}".format(label))
