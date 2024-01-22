from gui import (Button, Menu)

def make_title_page(app):
    def title_callback():
        app.set_active_page("main_menu")
    title_page = Menu("gui/images/title.png")
    enter_btn = Button(0, 0, 296, 128, title_callback)
    title_page.add_elements(enter_btn)
    app.add_page("title", title_page)
