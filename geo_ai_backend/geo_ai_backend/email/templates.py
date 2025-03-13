INVITE_USER_TEMPLATE = """
<html>
    <body style="margin: 0; padding: 0; box-sizing: border-box; font-family: Arial, Helvetica, sans-serif;">
        <div style="width: 100%; background: #efefef; border-radius: 10px; padding: 10px;">
            <div style="margin: 0 auto; width: 90%; text-align: center;">
                <h1 style="background-color: rgba(0, 53, 102, 1); padding: 5px 10px; border-radius: 5px; color: white;">{title}</h1>
                <div style="margin: 30px auto; background: white; width: 40%; border-radius: 10px; padding: 50px; text-align: center;">
                    <h3 style="margin-bottom: 100px; font-size: 24px;">{name}!</h3>
                    <a style="display: block; margin: 0 auto; border: none; background-color: rgba(255, 214, 10, 1); color: white; width: 200px; line-height: 24px; padding: 10px; font-size: 24px; border-radius: 10px; cursor: pointer; text-decoration: none;"
                        href="{link}"
                        target="_blank"
                    >
                        Сompletion of registration!
                    </a>
                </div>
            </div>
        </div>
    </body>
</html>
"""


RESTORE_ACCESS_TEMPLATE = """
<html>
    <body style="margin: 0; padding: 0; box-sizing: border-box; font-family: Arial, Helvetica, sans-serif;">
        <div style="width: 100%; background: #efefef; border-radius: 10px; padding: 10px;">
            <div style="margin: 0 auto; width: 90%; text-align: center;">
                <div style="margin: 30px auto; background: white; width: 40%; border-radius: 10px; padding: 50px; text-align: center;">
                    <h3 style="color:black; margin-bottom: 100px; font-size: 24px;">You can change your password by following the link</h3>
                    <a style="display: block; margin: 0 auto; border: none; background-color: rgba(255, 214, 10, 1); color: white; width: 200px; line-height: 24px; padding: 10px; font-size: 24px; border-radius: 10px; cursor: pointer; text-decoration: none;"
                        href="{link}"
                        target="_blank"
                    >
                        Change password
                    </a>
                </div>
            </div>
        </div>
    </body>
</html>
"""
