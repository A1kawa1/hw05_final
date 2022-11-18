from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.cache import cache
from http import HTTPStatus
from posts.models import Post, Group

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.guest_client = Client()
        cls.user2 = User.objects.create_user(username='alex')
        cls.authorized_client = Client()
        cls.authorized_client2 = Client()

        cls.templates = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
            f'/posts/{cls.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            'dfsdf': 'core/404.html'
        }

    def setUp(self):
        cache.clear()
        StaticURLTests.authorized_client.force_login(StaticURLTests.user2)
        StaticURLTests.authorized_client2.force_login(StaticURLTests.user)

    def tearDown(self):
        cache.clear()

    def test_homepage(self):
        """Проверка доступности адреса /"""
        response = StaticURLTests.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group(self):
        """Проверка доступности адреса /group/test_slug/"""
        response = StaticURLTests.guest_client.get(
            f'/group/{StaticURLTests.group.slug}/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile(self):
        """Проверка доступности адреса '/profile/auth/"""
        response = StaticURLTests.guest_client.get(
            f'/profile/{StaticURLTests.user.username}/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts(self):
        """Проверка доступности адреса /posts/1/"""
        response = StaticURLTests.guest_client.get(
            f'/posts/{StaticURLTests.post.id}/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_unlog(self):
        """Проверка перенаправления не авторизированного пользователя
        с /create/ на /auth/login/?next=/create/"""
        responce = StaticURLTests.guest_client.get('/create/', follow=True)
        self.assertRedirects(responce, '/auth/login/?next=/create/')

    def test_create(self):
        """Проверка доступности адреса /create/
        для авторизированного пользователя"""
        responce = StaticURLTests.authorized_client.get('/create/')
        self.assertEqual(responce.status_code, HTTPStatus.OK)

    def test_edit_unlog(self):
        """Проверка перенаправления не авторизированного пользователя
        с /posts/{id}/edit/ на /auth/login/?next=/posts/{id}/edit/"""
        id = StaticURLTests.post.id
        responce = StaticURLTests.guest_client.get(
            f'/posts/{id}/edit/',
            follow=True
        )
        self.assertRedirects(responce, f'/auth/login/?next=/posts/{id}/edit/')

    def test_edit_no_author(self):
        """Проверка перенаправления пользователя, не являющимся автором
        с /posts/{id}/edit/ на /posts/{id}/"""
        id = StaticURLTests.post.id
        responce = StaticURLTests.authorized_client.get(f'/posts/{id}/edit/',
                                                        follow=True)
        self.assertRedirects(responce, f'/posts/{id}/')

    def test_edit(self):
        """Проверка доступности адреса /posts/{id}/edit/ для автора"""
        id = StaticURLTests.post.id
        responce = StaticURLTests.authorized_client2.get(f'/posts/{id}/edit/',
                                                         follow=True)
        self.assertEqual(responce.status_code, HTTPStatus.OK)

    def test_unexsist(self):
        """Проверка ошибки 404 для несуществующей страницы"""
        responce = StaticURLTests.guest_client.get('/sdfsd/')
        self.assertEqual(responce.status_code, HTTPStatus.NOT_FOUND)

    def test_template(self):
        """Адрес из словаря template использует соответсвующий шаблон"""
        for url, template in StaticURLTests.templates.items():
            with self.subTest(url=url):
                response = StaticURLTests.authorized_client2.get(url)
                self.assertTemplateUsed(response, template, url)

    def test_comment_unlog(self):
        """Проверка перенаправления не авторизированного пользователя
        с /posts/{id}/comment/ на /auth/login/?next=/posts/{id}/comment/"""
        id = StaticURLTests.post.id
        responce = StaticURLTests.guest_client.get(
            f'/posts/{id}/comment/',
            follow=True
        )
        self.assertRedirects(
            responce,
            f'/auth/login/?next=/posts/{id}/comment/'
        )
