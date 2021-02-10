import click


def prompt(message, options=None):
    try:
        user_prompt_value = click.prompt(message, type=str)
        if user_prompt_value in options:
            return user_prompt_value
        else:
            raise ValueError
    except ValueError:
        return prompt(message, options)
