import os

import game
import persistance
import models


_HEX_COLOR_VALUES_BY_BRAND = {
    None: "#c3c3c3",
    models.Brand.TOWER: "#feac13",
    models.Brand.LUXOR: "#f52d2e",
    models.Brand.WORLDWIDE: "#7a4e28",
    models.Brand.AMERICAN: "#092053",
    models.Brand.FESTIVAL: "#207735",
    models.Brand.IMPERIAL: "#cf183e",
    models.Brand.CONTINENTAL: "#138199"
}


def take_move(request):
    x_string, y_string = request.form['grid_space'].split(',')
    x = int(x_string)
    y = int(y_string)

    brand_value = int(request.form['brand'])
    brand = None if brand_value == 0 else models.Brand(brand_value)

    old_state = persistance.get_state()
    new_state = game.place_tile(old_state, x, y, brand)

    persistance.set_state(new_state)

    return _format_state(new_state)


def _format_state(state):
    return "Yo, world!!!"
    # width = int(os.environ['WIDTH'])
    # length = int(os.environ['HEIGHT'])
    #
    # return render_template(
    #     'index.html',
    #     grid=state.grid,
    #     x_range=range(width),
    #     y_range=range(length),
    #     brands=[(0, '')] + [(brand.value, brand.name) for brand in models.Brand],
    #     hex_color_values_by_brand=_HEX_COLOR_VALUES_BY_BRAND)
