# Pro college API


## Авторизация
```http
POST /user/login
{
    "login": "user login",
    "password": "user password"
}
```

### Response
```json
{"access_token": "...", "user_id": "000"}
```

## Получение информации о пользователе
```http
GET /user/info?access_token=<ACCESS_TOKEN>
```

### Response
```json
{
    "main_info": {
        "Специальность": "Информационные системы и программирование",
        "форма обучения": "очная",
        "Группа": "XX.XX.XX.XX",
        "Классный руководитель": "..."
    },
    "user_info": {
        "name": "XXXXXXX XXXXXX",
        "image": "https......"
    },
    "today": {
        "title": "Среда, 11/09/2024",
        "lessons": [
            {
                "number": "4",
                "lesson_time": [
                    "14:00",
                    "15:30"
                ],
                "teacher": "XXX",
                "title": "XXXXXXX",
                "classroom": "XXXX"
            }
        ],
        "minutes": 270
    },
    "courses": [
        {
            "title": "XX курс",
            "courses": [
                {
                    "title": "XXXXXXXXXX",
                    "teacher": "XXXXX XXXXXXXXXXX XXXXXXXXXXX"
                }
            ]
        }
    ]
}
```


## Перемещение по дням расписания
```http
GET /user/day/{OFFSET}?access_token=<ACCESS_TOKEN>

OFFSET - целое число
например `-1` для сдвига на один день назад
или `9` для сдвига на 9 дней вперед
```

### Response
```json
{
    "title": "Суббота, 14/09/2024",
    "lessons": [
        {
            "number": "1",
            "lesson_time": [
                "8:15",
                "9:45"
            ],
            "teacher": "XXXXX",
            "title": "XXXXXXXXXX",
            "classroom": "XXX"
        }
    ],
    "minutes": 360
}
```
