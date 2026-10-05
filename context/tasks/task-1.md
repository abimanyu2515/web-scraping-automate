Generate reliable object names + robust selectors

- Right now you have entries like:

- `{
    "id": 1,
    "tag": "button",
    "text": "Login",
    "locator_type": "css",
    "locator": "#login-btn"
}`

- We want to move toward something like:

- `{
    "name": "login_button",
    "locator_type": "css",
    "locator": "#login-btn",
    "tag": "button",
    "text": "Login"
}`

- The important change is that name becomes the human-readable identifier used by your automation framework.

- For example:

    - login_button
    - username_input
    - password_input
    - forgot_password_link
    - signup_link