## Курсовой проект "Игра Что? Где? Когда?"
### Особенности реализации:
 - Асинхронный подход
 - Разделение на 4 микросервиса
 - Микросервисы общаются между собой через очереди RabbitMQ
 - Игроки могут участвовать одновременно в нескольких играх

### Запуск посредством Docker
`docker-compose up --build`