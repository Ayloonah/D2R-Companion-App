import re

# Each placeholder the game uses -> the regex that captures it
PLACEHOLDER_TO_REGEX = {"%+d": r"([+-]?\d+)",   # signed number, e.g. "+30"
                        "%d": r"(\d+)",         # plain number, e.g. "30"
                        "%s": r"(.+?)",         # some text, e.g. a skill name
                        "%%": "%"}              # a literal percent sign

# Splits a template into placeholders and plain text
# (%0-%9 are numbered placeholders, used by a couple of templates like "Reanimate as: %1")
PLACEHOLDER_PATTERN = re.compile(r"(%\+d|%d|%s|%%|%\d)")

def template_to_regex(template):
    """
    Convert a game stat template (printf style, e.g. "%+d%% Faster Cast Rate")
    into a compiled regex that matches a full tooltip line and captures its values.

    Plain text is escaped so characters like ( ) and + are matched literally.
    Placeholders become capture groups. The pattern is anchored with ^ and $
    so it only matches when it explains the entire line.

    Example:
        template_to_regex("%+d%% Faster Cast Rate").match("+30% Faster Cast Rate").groups()
        -> ('+30',)
    """
    parts = []

    for piece in PLACEHOLDER_PATTERN.split(template):
        if piece in PLACEHOLDER_TO_REGEX:
            parts.append(PLACEHOLDER_TO_REGEX[piece])
        elif re.fullmatch(r"%\d", piece):
            parts.append(r"(.+?)")      # numbered placeholder: capture whatever is there
        else:
            parts.append(re.escape(piece))

    return re.compile("^" + "".join(parts) + "$", re.IGNORECASE)