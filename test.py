import re


def sanitize_for_exfat(name):
    # Define a regular expression pattern for disallowed characters
    # Includes control characters (U+0000 to U+001F), and specific symbols
    pattern = r'[\x00-\x1F"*/:<>?\\|]'

    # Replace any occurrence of the disallowed characters with an underscore
    sanitized_name = re.sub(pattern, '_', name)

    # Additional rule: Remove leading and trailing spaces
    sanitized_name = sanitized_name.strip()

    return sanitized_name


# Example usage
original_name = 'example<name>:*?|'
sanitized_name = sanitize_for_exfat(original_name)
print(f'Original: {original_name}')
print(f'Sanitized: {sanitized_name}')
