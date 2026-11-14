"""The 蛇記冰室 menu and shops (fictional). Used by `manage.py seed`."""
from decimal import Decimal as D

# (slug, name_en, name_zh, description_en, description_zh, category, price, iced_surcharge, iced_only, popularity)
MENU = [
    ("milk-tea", "HK-style milk tea", "港式奶茶", "Silky 'pantyhose' tea with evaporated milk", "絲襪拉茶，淡奶香滑", "drink", D("22"), D("3"), False, 14),
    ("lemon-tea", "Lemon tea", "檸檬茶", "Ceylon tea, fresh lemon slices", "錫蘭紅茶配鮮檸檬", "drink", D("22"), D("3"), False, 12),
    ("yuenyeung", "Yuenyeung", "鴛鴦", "Coffee meets milk tea", "咖啡撞奶茶", "drink", D("23"), D("3"), False, 6),
    ("coffee", "Coffee", "咖啡", "Strong and smooth, with evaporated milk", "香濃咖啡", "drink", D("22"), D("3"), False, 4),
    ("lemon-coke", "Lemon coke", "檸樂", "Cola with lemon slices", "可樂加鮮檸檬", "drink", D("24"), D("3"), False, 4),
    ("honey-lemon", "Honey lemon", "檸蜜", "Fresh lemon with honey", "鮮檸檬配蜜糖", "drink", D("24"), D("3"), False, 3),
    ("horlicks", "Horlicks", "好立克", "Malted milk, hot or cold", "麥芽牛奶", "drink", D("24"), D("3"), False, 2),
    ("red-bean-ice", "Red bean ice", "紅豆冰", "Sweet red beans, evaporated milk, crushed ice", "紅豆、淡奶、碎冰", "drink", D("30"), D("0"), True, 3),
    ("pineapple-bun-butter", "Pineapple bun with butter", "菠蘿油", "Warm crackly bun, thick slab of cold butter", "熱辣辣菠蘿包夾厚牛油", "toast", D("20"), None, False, 9),
    ("french-toast", "HK French toast", "西多士", "Deep-fried, peanut butter, golden syrup", "炸多士夾花生醬，淋糖漿", "toast", D("32"), None, False, 7),
    ("condensed-milk-toast", "Condensed milk toast", "奶油多", "Thick toast, butter and condensed milk", "厚多士配牛油煉奶", "toast", D("18"), None, False, 4),
    ("ham-egg-sandwich", "Ham & egg sandwich", "火腿蛋治", "Fluffy egg, ham, white bread", "滑蛋火腿三文治", "toast", D("28"), None, False, 5),
    ("egg-tart", "Egg tart", "蛋撻", "Fresh from the oven", "新鮮出爐", "toast", D("12"), None, False, 6),
    ("macaroni-ham-soup", "Macaroni in ham soup", "火腿通粉", "The breakfast classic", "經典早餐", "noodles", D("36"), None, False, 6),
    ("spam-egg-noodles", "Spam & egg instant noodles", "餐蛋公仔麵", "Instant noodles, luncheon meat, fried egg", "公仔麵配午餐肉煎蛋", "noodles", D("42"), None, False, 8),
    ("satay-beef-noodles", "Satay beef noodles", "沙嗲牛肉麵", "Tender beef in rich satay sauce", "嫩牛肉配濃郁沙嗲汁", "noodles", D("46"), None, False, 6),
    ("beef-chow-fun", "Beef chow fun", "乾炒牛河", "Wok-fried rice noodles with beef", "鑊氣十足", "noodles", D("68"), None, False, 5),
    ("baked-pork-chop-rice", "Baked pork chop rice", "焗豬扒飯", "Tomato sauce, cheese, fried rice", "茄汁芝士焗豬扒飯", "rice", D("72"), None, False, 8),
    ("char-siu-egg-rice", "Char siu & fried egg rice", "叉燒煎蛋飯", "Honey-glazed BBQ pork, runny egg", "蜜汁叉燒配流心煎蛋", "rice", D("58"), None, False, 6),
    ("curry-beef-brisket-rice", "Curry beef brisket rice", "咖喱牛腩飯", "Slow-cooked brisket, HK curry", "慢燉牛腩，港式咖喱", "rice", D("68"), None, False, 5),
    ("hainan-chicken-rice", "Hainanese chicken rice", "海南雞飯", "Poached chicken, fragrant rice, ginger sauce", "白切雞配油飯薑蓉", "rice", D("66"), None, False, 5),
    ("curry-fish-balls", "Curry fish balls", "咖喱魚蛋", "Street-food favourite", "街頭小食", "snack", D("22"), None, False, 4),
    ("chicken-wings", "Fried chicken wings", "炸雞翼", "Crispy, three pieces", "香脆三隻", "snack", D("38"), None, False, 3),
]

# (id, name_en, name_zh, district, seats, traffic)
SHOPS = [
    (1, "Snake Kee Mong Kok", "蛇記冰室 旺角店", "Yau Tsim Mong", 80, 1.6),
    (2, "Snake Kee Sham Shui Po", "蛇記冰室 深水埗店", "Sham Shui Po", 60, 1.3),
    (3, "Snake Kee Central", "蛇記冰室 中環店", "Central & Western", 50, 1.4),
    (4, "Snake Kee Causeway Bay", "蛇記冰室 銅鑼灣店", "Wan Chai", 70, 1.5),
    (5, "Snake Kee Kwun Tong", "蛇記冰室 觀塘店", "Kwun Tong", 90, 1.4),
    (6, "Snake Kee Tsuen Wan", "蛇記冰室 荃灣店", "Tsuen Wan", 70, 1.1),
    (7, "Snake Kee Sha Tin", "蛇記冰室 沙田店", "Sha Tin", 80, 1.2),
    (8, "Snake Kee Tuen Mun", "蛇記冰室 屯門店", "Tuen Mun", 60, 0.9),
    (9, "Snake Kee Yuen Long", "蛇記冰室 元朗店", "Yuen Long", 60, 0.9),
    (10, "Snake Kee North Point", "蛇記冰室 北角店", "Eastern", 50, 0.9),
    (11, "Snake Kee Tai Po", "蛇記冰室 大埔店", "Tai Po", 50, 0.7),
    (12, "Snake Kee Tseung Kwan O", "蛇記冰室 將軍澳店", "Sai Kung", 70, 1.0),
    (13, "Snake Kee Kowloon Bay", "蛇記冰室 九龍灣店", "Kwun Tong", 60, 1.0),
    (14, "Snake Kee To Kwa Wan", "蛇記冰室 土瓜灣店", "Kowloon City", 40, 0.7),
    (15, "Snake Kee Sheung Wan", "蛇記冰室 上環店", "Central & Western", 40, 0.8),
    (16, "Snake Kee Aberdeen", "蛇記冰室 香港仔店", "Southern", 40, 0.6),
    (17, "Snake Kee Tung Chung", "蛇記冰室 東涌店", "Islands", 50, 0.6),
    (18, "Snake Kee Kwai Chung", "蛇記冰室 葵涌店", "Kwai Tsing", 60, 0.9),
    (19, "Snake Kee Wong Tai Sin", "蛇記冰室 黃大仙店", "Wong Tai Sin", 50, 0.8),
    (20, "Snake Kee Kowloon Tong", "蛇記冰室 九龍塘店", "Kowloon City", 40, 0.7),
]

SOLD_OUT = {"red-bean-ice"}  # no photo yet, so it's "sold out" today

SWEETNESS = ["正常", "少甜", "走甜"]   # what the current ordering app sends
ICE = ["正常冰", "少冰", "走冰"]
