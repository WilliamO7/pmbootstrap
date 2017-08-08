import re


class ShellParser:
    """Parser for global variables in shell script files"""

    REGEX_VARIABLE = re.compile(r"^([a-zA-Z0-9_]+)=(\"|)(.*?)(\"|)$")
    REGEX_NAME = re.compile(r"[a-zA-Z0-9_]")

    STATE_RAW = 0
    STATE_SUBST_COMPLEX = 1
    STATE_SUBST_SIMPLE = 2

    def __init__(self, data, environment=None):
        """Parse shell script for global variables

        :param data: Shell script contents or file handle
        :param environment: dictionary of variables defined in the environment
        """
        if hasattr(data, 'read'):
            with data:
                self.raw = data.read()
        else:
            self.raw = data
        self.variables = {}

        # Add provided environment variables to the list of defined variables
        # so they can be referenced by script variables
        if environment is not None:
            self.variables.update(environment)

        self._parse()

    def _parse(self):
        """ Parse the contents of a shell script line-by-line """
        for line in self.raw.splitlines():
            variable = self.REGEX_VARIABLE.match(line)
            if variable is not None:
                name, startquote, value, endquote = variable.groups()
                if startquote == endquote:
                    result = self._process_substitutions(value)
                    self.variables[name] = result
                else:
                    # TODO: Implement multiline variables
                    pass

    def _process_substitutions(self, value):
        """ Parse contents of variable assignment with a state machine

        :param value: Right hand side of the variable assignment
        :return: Evaluated version of right hand side expression
        """

        # Add a extra char to the end of the data to trigger the last iteration of the state machine in all cases
        value += "\0"
        state = self.STATE_RAW

        # Stack of interpolations in ${...} expressions (for nesting)
        stack = []

        # Buffer for simple substitutions $...
        simple = ""

        # Output buffer for the processed data
        processed = ""

        i = 0
        while i < len(value):
            char = value[i]

            if state == self.STATE_RAW:

                # Switch to one of the substitutions states on encountering a $
                if char != "$":
                    processed += char
                else:
                    if value[i + 1] == "{":
                        state = self.STATE_SUBST_COMPLEX
                    else:
                        state = self.STATE_SUBST_SIMPLE

            # Parse $... expression
            elif state == self.STATE_SUBST_SIMPLE:
                if self.REGEX_NAME.match(char):
                    simple += char
                else:
                    processed += self.variables[simple]
                    simple = ""
                    state = self.STATE_RAW
                    i -= 1

            # Parse ${...} expression with nesting
            elif state == self.STATE_SUBST_COMPLEX:
                # Start the first stack level
                if char == "{":
                    stack.append("")

                # Add deeper stack level on encountering nested variable
                elif char == "$" and value[i + 1] == "{":
                    stack.append("")
                    i += 1

                # End the current stack level
                elif char == "}":
                    label = stack.pop()
                    label_value = self._process_substitution_value(label)

                    if len(stack) > 0:
                        # Append completed stack level to the previous stack
                        stack[-1] += label_value
                    else:
                        # This was the last nesting level, append the result to the output buffer
                        processed += label_value
                        state = self.STATE_RAW

                else:
                    stack[-1] += char
            i += 1
        return processed[0:-1]

    def _process_substitution_value(self, label):
        """ Process ${...} expressions with a few variations

        :param label: Contents of the ${...} expression
        :return: Evaluated result of the expression
        """

        # ${variable}
        # Return a variable if it's a simple substitution.
        if label in self.variables:
            return self.variables[label]

        # ${variable:-default}
        # Return default value if variable is unset or empty
        if ':-' in label:
            lookup, default = label.split(':')
            default = default[1:]
            if lookup in self.variables and self.variables[lookup] != "":
                return self.variables[lookup]
            else:
                return default

        # ${variable:=default}
        # Assign and return default if variable is unset or empty
        if ':=' in label:
            lookup, default = label.split(':')
            default = default[1:]
            if lookup in self.variables and self.variables[lookup] != "":
                return self.variables[lookup]
            else:
                self.variables[lookup] = default
                return default

        # ${variable=default}
        # Assign and return default if variable is unset
        if '=' in label:
            lookup, default = label.split('=')
            if lookup in self.variables:
                return self.variables[lookup]
            else:
                self.variables[lookup] = default
                return default

        # ${#variable}
        # Return length of variable contents
        #
        # ${variable#pattern}
        # Remove pattern from start of variable value if it exists
        if '#' in label:
            variable, pattern = label.split('#')
            if variable == "":
                return str(len(self.variables[pattern]))
            variable = self.variables[variable]
            if variable[0:len(pattern)] == pattern:
                return variable[len(pattern):]
            return variable

        raise KeyError("Could not find variable {}".format(label))
