# Foodgram

**Foodgram** — это открытый проект-блог, который позволяет пользователям делиться рецептами своих уникальных блюд, продвигая *кулинарные шедевры* в массы. 
Детальное описание приготовления яств и удобный список ингредиентов(*который вы сможете скачать, чтобы точно ничего не потерять*) позволят вам ощутить мириады гастрономических вкусов, сделав привычные будни чем-то по-настоящему уникальным. А возможность подписаться на пользователей позволит отслеживать кулинарные новинки и следить за современными тенденциями в приготовлении пищи(*теперь вы точно ничего не пропустите!*).

**Добавляйте любимые блюда в «избранное» и создавайте свои шедевры! Встретимся на кухне!**


## Технический стек

- **Backend**: Django, Django REST Framework
- **CI/CD**: GitHub Actions
- **Контейнеризация**: Docker
- **Веб-сервер**: Nginx

## Внешний вид сайта

### **Админка**
![photo_2025-10-15_15-30-44](https://github.com/user-attachments/assets/aefd3859-74fc-4bc0-9fa8-53de035f4bf4)
![photo_2025-10-15_15-30-44 (2)](https://github.com/user-attachments/assets/39335f12-1e7b-41a8-a030-c531849f4f5c)

### **Регистрация**
![photo_2025-10-11_10-36-07](https://github.com/user-attachments/assets/364f6044-92a9-40e8-8287-5c0517fafa54)

### **Главная страница**
<img width="1155" height="921" alt="Снимок экрана 2025-10-27 171135" src="https://github.com/user-attachments/assets/87dd93e2-29f5-4c6a-a009-c706ee692af6" />
<img width="1190" height="926" alt="Снимок экрана 2025-10-27 171156" src="https://github.com/user-attachments/assets/7cac2d7d-8c87-4504-9f3c-ddb285e1f88b" />
<img width="1373" height="927" alt="image" src="https://github.com/user-attachments/assets/0889df18-5251-44aa-b02f-c8513142289e" />

### **Подписки**
<img width="1268" height="912" alt="Снимок экрана 2025-10-27 171409" src="https://github.com/user-attachments/assets/8d5b3d10-b167-45a3-b60f-504b3fa47e10" />

### **Избранное**
<img width="1331" height="916" alt="image" src="https://github.com/user-attachments/assets/3e73f66e-03c1-45b8-aa57-b3b08e3f9d3d" />

### **Список покупок**
<img width="1373" height="927" alt="image" src="https://github.com/user-attachments/assets/ae0fbc17-8145-43d9-92b8-8f096303aef4" />


## Установка и развертывание

1. Клонируйте репозиторий:
```bash
git clone <название-репозитория>
cd <название-репозитория>
```
2. Создать и активировать виртуальную среду:
```bash
python -m venv venv
source venv/Scripts/activate
```
3. Установить зависимости из файла requirements.txt:
```bash
cd backend/
python -m pip install --upgrade pip
pip install -r requirements.txt
```
4. Выполнить миграции:
```bash
python manage.py migrate
```
5. Скачивание списка игредиентов:
```bash
python manage.py load_ingredients
```

### Запуск проекта
**Докер**
```bash
cd infra/
docker-compose up --build -d
```
**Запуск локального сервера**
```bash
cd backend/
python manage.py runserver
```

### Сервер
- **Производственный сервер**: [http://51.250.24.182](http://51.250.24.182)
- **Локальный сервер**: [http://localhost](http://localhost)

### Документация и администрирование
- **Frontend веб-приложение**: [http://localhost](http://localhost) - основное веб-приложение
- **API документация**: [http://localhost/api/docs/](http://localhost/api/docs/) - спецификация API (Swagger/ReDoc)
- **Админка Django**: [http://localhost/admin/](http://localhost/admin/) - панель администратора

## Автор
[Поночовный Дмитрий Витальевич] - [https://github.com/Dmitriytechf]
