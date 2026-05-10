PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    language_code TEXT DEFAULT 'ru',
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP,
                    searches_count INTEGER DEFAULT 0,
                    chats_count INTEGER DEFAULT 0,
                    reputation INTEGER DEFAULT 100,
                    is_banned BOOLEAN DEFAULT FALSE,
                    ban_reason TEXT,
                    ban_until TIMESTAMP,
                    total_messages_sent INTEGER DEFAULT 0
                , is_premium BOOLEAN DEFAULT 0, premium_until TIMESTAMP, user_status TEXT DEFAULT "guest", guest_upgrade_progress INTEGER DEFAULT 0, chat_name TEXT DEFAULT NULL, gender TEXT DEFAULT 'unknown', age INTEGER DEFAULT NULL, show_age BOOLEAN DEFAULT 0, show_gender BOOLEAN DEFAULT 0, photo_file_id TEXT, photo_updated_at TIMESTAMP, main_photo_file_id TEXT);
INSERT INTO users VALUES(5289967568,'cath_diog','cath diog 🤬','','ru','2026-02-03 14:37:04','2026-05-05 11:51:33',142,65,25,0,NULL,NULL,38,1,'2026-05-01 13:29:48','guest',0,NULL,'unknown',18,0,0,NULL,NULL,NULL);
INSERT INTO users VALUES(7096355763,'aniko_so','‌‎ Aniko‌‎','','ru','2026-02-02 10:15:33','2026-05-05 11:51:30',364,80,45,0,NULL,NULL,189,0,NULL,'admin',0,'Aniko','male',26,0,0,'AgACAgIAAxkBAAILUGnXb9dja3KnqpFqtnX-FPdevsicAAIBE2sbWZC4SoQbnsOuhpuGAQADAgADeQADOwQ','2026-04-09 09:22:31',NULL);
INSERT INTO users VALUES(7171026431,'love_or_sympathy','Тася','Хьюго','ru','2026-02-03 22:26:54','2026-02-03 22:26:54',1,0,25,0,NULL,NULL,0,0,NULL,'guest',0,NULL,'unknown',NULL,0,0,NULL,NULL,NULL);
INSERT INTO users VALUES(8337756676,'Аноним 6676','ANNA','','ru','2026-04-21 12:53:27','2026-04-23 00:41:18',4,2,25,0,NULL,NULL,71,0,NULL,'guest',0,NULL,'unknown',NULL,0,0,NULL,NULL,NULL);
INSERT INTO users VALUES(8427551862,'Аноним 1862','Gor','','ru','2026-04-20 13:51:24','2026-04-20 13:51:24',1,1,25,0,NULL,NULL,7,0,NULL,'guest',0,NULL,'unknown',NULL,0,0,NULL,NULL,NULL);
INSERT INTO users VALUES(8745654836,'Niickks','Nn','','ru','2026-04-14 14:59:23','2026-04-14 15:53:19',1,0,25,0,NULL,NULL,30,0,NULL,'guest',0,NULL,'unknown',NULL,0,0,NULL,NULL,NULL);
CREATE TABLE active_chats (
                    user1_id INTEGER,
                    user2_id INTEGER,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user1_id, user2_id),
                    FOREIGN KEY (user1_id) REFERENCES users (user_id) ON DELETE CASCADE,
                    FOREIGN KEY (user2_id) REFERENCES users (user_id) ON DELETE CASCADE
                );
INSERT INTO active_chats VALUES(5289967568,7096355763,'2026-05-05 11:06:48');
INSERT INTO active_chats VALUES(7096355763,5289967568,'2026-05-05 11:51:42');
CREATE TABLE search_queue (
                    user_id INTEGER PRIMARY KEY,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    search_timeout INTEGER DEFAULT 30,
                    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
                );
CREATE TABLE chat_history (
                    chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user1_id INTEGER,
                    user2_id INTEGER,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP,
                    duration_seconds INTEGER,
                    user1_left_first BOOLEAN,
                    user2_left_first BOOLEAN, chat_token TEXT,
                    FOREIGN KEY (user1_id) REFERENCES users (user_id),
                    FOREIGN KEY (user2_id) REFERENCES users (user_id)
                );
INSERT INTO chat_history VALUES(1,5289967568,7096355763,'2026-03-27 08:18:54','2026-03-27 11:20:18',10884,1,0,NULL);
INSERT INTO chat_history VALUES(2,5289967568,7096355763,'2026-03-27 08:49:16','2026-03-27 11:54:23',11107,1,0,NULL);
INSERT INTO chat_history VALUES(3,5289967568,7096355763,'2026-03-27 08:55:30','2026-03-27 11:55:35',10805,1,0,NULL);
INSERT INTO chat_history VALUES(4,7096355763,5289967568,'2026-03-27 08:54:18','2026-03-27 11:55:58',10900,1,0,NULL);
INSERT INTO chat_history VALUES(5,7096355763,5289967568,'2026-04-04 11:18:52','2026-04-04 14:21:16',10944,1,0,NULL);
INSERT INTO chat_history VALUES(6,5289967568,7096355763,'2026-04-07 10:28:43','2026-04-07 13:32:48',11045,1,0,NULL);
INSERT INTO chat_history VALUES(7,5289967568,7096355763,'2026-04-07 11:20:04','2026-04-07 14:21:17',10873,1,0,NULL);
INSERT INTO chat_history VALUES(8,7096355763,5289967568,'2026-04-18 12:49:49','2026-04-18 15:50:34',10845,1,0,NULL);
INSERT INTO chat_history VALUES(9,5289967568,7096355763,'2026-04-21 11:32:23','2026-04-21 11:32:23',0,1,0,NULL);
INSERT INTO chat_history VALUES(10,7096355763,5289967568,'2026-04-21 11:38:47','2026-04-21 11:39:38',51,1,0,NULL);
INSERT INTO chat_history VALUES(11,5289967568,7096355763,'2026-04-21 11:55:26','2026-04-21 11:56:03',37,1,0,NULL);
INSERT INTO chat_history VALUES(12,5289967568,7096355763,'2026-04-21 11:56:21','2026-04-21 11:56:27',6,1,0,NULL);
INSERT INTO chat_history VALUES(13,7096355763,5289967568,'2026-04-21 12:31:31','2026-04-21 12:31:47',16,1,0,NULL);
INSERT INTO chat_history VALUES(14,7096355763,5289967568,'2026-04-21 13:33:49','2026-04-21 13:33:54',5,1,0,NULL);
INSERT INTO chat_history VALUES(15,5289967568,7096355763,'2026-04-22 12:12:00','2026-04-22 12:12:36',36,1,0,NULL);
INSERT INTO chat_history VALUES(16,5289967568,7096355763,'2026-04-24 13:47:10','2026-04-24 13:47:53',43,1,0,NULL);
INSERT INTO chat_history VALUES(17,5289967568,7096355763,'2026-04-24 13:50:29','2026-04-24 13:51:06',37,1,0,NULL);
INSERT INTO chat_history VALUES(18,5289967568,7096355763,'2026-04-24 13:59:23','2026-04-24 13:59:26',3,1,0,NULL);
INSERT INTO chat_history VALUES(19,5289967568,7096355763,'2026-04-25 19:07:01','2026-04-25 19:07:08',7,1,0,NULL);
INSERT INTO chat_history VALUES(20,7096355763,5289967568,'2026-04-25 20:09:20','2026-04-25 20:09:25',5,1,0,NULL);
INSERT INTO chat_history VALUES(21,5289967568,7096355763,'2026-04-25 20:13:43','2026-04-25 20:14:19',36,1,0,NULL);
INSERT INTO chat_history VALUES(22,5289967568,7096355763,'2026-04-26 10:28:42','2026-04-26 10:28:44',2,1,0,NULL);
INSERT INTO chat_history VALUES(23,5289967568,7096355763,'2026-04-27 10:45:53','2026-04-27 10:46:31',38,1,0,NULL);
INSERT INTO chat_history VALUES(24,5289967568,7096355763,'2026-04-28 14:18:57','2026-04-28 14:19:28',31,1,0,NULL);
INSERT INTO chat_history VALUES(25,5289967568,7096355763,'2026-04-28 14:42:10','2026-04-28 14:42:39',29,1,0,NULL);
INSERT INTO chat_history VALUES(26,5289967568,7096355763,'2026-04-28 14:51:14','2026-04-28 14:51:37',23,1,0,NULL);
INSERT INTO chat_history VALUES(27,5289967568,7096355763,'2026-04-28 14:57:48','2026-04-28 14:58:22',34,1,0,NULL);
INSERT INTO chat_history VALUES(28,5289967568,7096355763,'2026-04-28 15:25:26','2026-04-28 15:25:30',4,1,0,NULL);
CREATE TABLE reports (
                        report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        reporter_id INTEGER,
                        reported_id INTEGER,
                        reason TEXT NOT NULL,
                        chat_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'pending',
                        admin_notes TEXT,
                        admin_id INTEGER,
                        resolved_at TIMESTAMP,
                        FOREIGN KEY (reporter_id) REFERENCES users (user_id),
                        FOREIGN KEY (reported_id) REFERENCES users (user_id),
                        FOREIGN KEY (chat_id) REFERENCES chat_history (chat_id),
                        FOREIGN KEY (admin_id) REFERENCES users (user_id)
                    );
INSERT INTO reports VALUES(1,7096355763,5289967568,'Другое',NULL,'2026-04-21 10:34:00','confirm','',7096355763,'2026-04-23 06:23:13');
INSERT INTO reports VALUES(2,7096355763,5289967568,'Другое',NULL,'2026-04-22 09:12:56','confirm','',7096355763,'2026-04-23 06:23:03');
INSERT INTO reports VALUES(3,5289967568,7096355763,'Другое',NULL,'2026-04-24 09:23:17','confirm','',7096355763,'2026-04-24 11:01:54');
INSERT INTO reports VALUES(4,7096355763,5289967568,'Другое',NULL,'2026-04-25 17:14:38','confirm','',7096355763,'2026-05-05 11:14:53');
INSERT INTO reports VALUES(5,7096355763,5289967568,'Другое',NULL,'2026-04-26 07:28:59','confirm','',7096355763,'2026-05-05 11:14:40');
INSERT INTO reports VALUES(6,5289967568,7096355763,'Реклама/спам',NULL,'2026-04-27 07:46:47','confirm','',7096355763,'2026-04-28 12:01:27');
INSERT INTO reports VALUES(7,5289967568,7096355763,'Другое',NULL,'2026-04-27 07:47:14','confirm','',7096355763,'2026-04-28 12:01:15');
INSERT INTO reports VALUES(8,5289967568,7096355763,'Другое',5289967568,'2026-04-28 11:52:14','confirm','',7096355763,'2026-04-28 12:00:46');
INSERT INTO reports VALUES(9,7096355763,5289967568,'Пользовательский текст: test test test',7096355763,'2026-04-28 11:59:41','confirm','',7096355763,'2026-04-28 12:00:30');
INSERT INTO reports VALUES(10,7096355763,5289967568,'Разжигание ненависти',NULL,'2026-05-05 11:05:14','reject','',7096355763,'2026-05-05 11:14:20');
INSERT INTO reports VALUES(11,7096355763,5289967568,'18+ контент',NULL,'2026-05-05 11:07:08','reject','',7096355763,'2026-05-05 11:14:31');
CREATE TABLE feedback (
                        feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        text TEXT NOT NULL,
                        rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    );
CREATE TABLE message_stats (
                        stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        date DATE,
                        messages_sent INTEGER DEFAULT 0,
                        messages_received INTEGER DEFAULT 0,
                        FOREIGN KEY (user_id) REFERENCES users (user_id),
                        UNIQUE(user_id, date)
                    );
CREATE TABLE topics (
                        topic_id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        emoji TEXT,
                        description TEXT,
                        is_premium BOOLEAN DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
INSERT INTO topics VALUES(1,'Ролевые игры','🎭','Ролевые игры, D&D, живые действия',0,'2026-05-05 11:51:22');
INSERT INTO topics VALUES(2,'Мемы','😂','Мемы, юмор, приколы',0,'2026-05-05 11:51:22');
INSERT INTO topics VALUES(3,'Одиночество','🌌','Разговоры по душам, философия',0,'2026-05-05 11:51:22');
INSERT INTO topics VALUES(4,'Игры','🎮','Видеоигры, настолки, киберспорт',0,'2026-05-05 11:51:22');
INSERT INTO topics VALUES(5,'Флирт','💘','Флирт, знакомства, отношения',0,'2026-05-05 11:51:22');
INSERT INTO topics VALUES(6,'Путешествия','✈️','Туризм, страны, культура',0,'2026-05-05 11:51:22');
INSERT INTO topics VALUES(7,'IT. Компьютеры','💻','Программирование, технологии',0,'2026-05-05 11:51:22');
INSERT INTO topics VALUES(8,'Музыка','🎵','Музыка, концерты',0,'2026-05-05 11:51:22');
INSERT INTO topics VALUES(9,'Авто','🚗','Авто, Мото и т.п.',0,'2026-05-05 11:51:22');
INSERT INTO topics VALUES(10,'Аниме','🇯🇵','Аниме, манга и т.д.',0,'2026-05-05 11:51:22');
INSERT INTO topics VALUES(11,'Фильмы','🎬','Кино, сериалы',0,'2026-05-05 11:51:22');
INSERT INTO topics VALUES(12,'Питомцы','🐕','Домашние животные, уход',0,'2026-05-05 11:51:22');
INSERT INTO topics VALUES(13,'Книги','📚','Литература, аудиокниги',0,'2026-05-05 11:51:22');
INSERT INTO topics VALUES(14,'Спорт','⚽','Футбол, хоккей, фитнес',0,'2026-05-05 11:51:22');
CREATE TABLE user_topics (
                        user_id INTEGER,
                        topic_id INTEGER,
                        selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
                        FOREIGN KEY (topic_id) REFERENCES topics (topic_id) ON DELETE CASCADE,
                        PRIMARY KEY (user_id, topic_id)
                    );
INSERT INTO user_topics VALUES(7171026431,3,'2026-02-03 22:29:20');
INSERT INTO user_topics VALUES(8337756676,5,'2026-04-21 14:05:21');
INSERT INTO user_topics VALUES(8337756676,1,'2026-04-21 14:05:25');
INSERT INTO user_topics VALUES(8337756676,3,'2026-04-21 14:05:31');
INSERT INTO user_topics VALUES(5289967568,8,'2026-04-27 06:36:23');
INSERT INTO user_topics VALUES(7096355763,5,'2026-04-29 21:02:25');
CREATE TABLE user_photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    photo_file_id TEXT,
    position INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, photo_key TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE TABLE user_daily_chats (
    user_id INTEGER,
    date TEXT,
    chats_count INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, date),
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);
INSERT INTO user_daily_chats VALUES(7096355763,'2026-04-28',5);
INSERT INTO user_daily_chats VALUES(7096355763,'2026-04-29',1);
INSERT INTO user_daily_chats VALUES(7096355763,'2026-05-05',12);
CREATE TABLE ai_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    ai_name TEXT,
                    ai_age INTEGER,
                    ai_gender TEXT,
                    topic TEXT,
                    rating TEXT,
                    is_complaint BOOLEAN DEFAULT 0,
                    complaint_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO ai_feedback VALUES(1,7096355763,NULL,NULL,NULL,NULL,'good',0,NULL,'2026-04-22 09:38:46');
INSERT INTO ai_feedback VALUES(2,7096355763,NULL,NULL,NULL,NULL,NULL,1,'Выдаёт себя за девушку','2026-04-22 09:40:19');
INSERT INTO ai_feedback VALUES(3,7096355763,NULL,NULL,NULL,NULL,NULL,1,'Реклама/спам','2026-04-22 09:57:32');
INSERT INTO ai_feedback VALUES(4,7096355763,NULL,NULL,NULL,NULL,NULL,1,'Реклама/спам','2026-04-22 10:16:14');
INSERT INTO ai_feedback VALUES(5,7096355763,NULL,NULL,NULL,NULL,NULL,1,'Реклама/спам','2026-04-22 10:21:53');
INSERT INTO ai_feedback VALUES(6,7096355763,NULL,NULL,NULL,NULL,NULL,1,'Реклама/спам','2026-04-22 10:29:09');
INSERT INTO ai_feedback VALUES(7,7096355763,'Настя',30,'female','обычный чат',NULL,1,'Реклама/спам','2026-04-22 10:32:46');
INSERT INTO ai_feedback VALUES(8,7096355763,'Лена',19,'female','обычный чат','good',0,NULL,'2026-04-22 10:33:35');
INSERT INTO ai_feedback VALUES(9,7096355763,'Рома',27,'male','обычный чат','bad',0,NULL,'2026-04-22 10:34:16');
INSERT INTO ai_feedback VALUES(10,5289967568,NULL,NULL,NULL,NULL,NULL,1,'Пользовательский текст: Долго думает','2026-04-27 06:42:02');
INSERT INTO ai_feedback VALUES(11,5289967568,'Катя',29,'female','Музыка',NULL,1,'Реклама/спам','2026-04-27 07:45:25');
INSERT INTO ai_feedback VALUES(12,7096355763,NULL,NULL,NULL,NULL,NULL,1,'Пользовательский текст: чушь несёт','2026-04-29 21:06:25');
INSERT INTO ai_feedback VALUES(13,7096355763,NULL,NULL,NULL,NULL,NULL,1,'Пользовательский текст: Тест жалобы на бота...','2026-05-05 06:33:40');
CREATE TABLE admin_pins (
    id INTEGER PRIMARY KEY,
    pin TEXT NOT NULL,
    created_by INTEGER,
    expires_at DATETIME
);
CREATE TABLE user_ratings (
    id INTEGER PRIMARY KEY,
    rater_id INTEGER,
    rated_id INTEGER,
    rating TEXT,
    chat_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, chat_token TEXT,
    UNIQUE(rater_id, rated_id, chat_id)
);
INSERT INTO sqlite_sequence VALUES('chat_history',28);
INSERT INTO sqlite_sequence VALUES('user_photos',12);
INSERT INTO sqlite_sequence VALUES('reports',11);
INSERT INTO sqlite_sequence VALUES('ai_feedback',13);
CREATE INDEX idx_users_banned ON users(is_banned);
CREATE INDEX idx_chat_history_users ON chat_history(user1_id, user2_id);
CREATE INDEX idx_chat_history_time ON chat_history(started_at);
CREATE INDEX idx_reports_status ON reports(status);
CREATE INDEX idx_reports_reported ON reports(reported_id);
CREATE INDEX idx_feedback_rating ON feedback(rating);
CREATE INDEX idx_users_activity ON users(last_activity);
COMMIT;
