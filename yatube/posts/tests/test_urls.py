from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.cache import cache
from posts.models import Post, Group, Follow

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

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='alex')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(StaticURLTests.user)
        self.templates = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            'dfsdf': 'core/404.html'
        }

    def test_homepage(self):
        """Проверка доступности адреса /"""
        response = self.guest_client.get('/')
        self.assertEqual(response.reason_phrase, 'OK')

    def test_group(self):
        """Проверка доступности адреса /group/test_slug/"""
        response = self.guest_client.get('/group/test_slug/')
        self.assertEqual(response.reason_phrase, 'OK')

    def test_profile(self):
        """Проверка доступности адреса '/profile/auth/"""
        response = self.guest_client.get('/profile/auth/')
        self.assertEqual(response.reason_phrase, 'OK')

    def test_posts(self):
        """Проверка доступности адреса /posts/1/"""
        response = self.guest_client.get('/posts/1/')
        self.assertEqual(response.reason_phrase, 'OK')

    def test_create_unlog(self):
        """Проверка перенаправления не авторизированного пользователя
        с /create/ на /auth/login/?next=/create/"""
        responce = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(responce, '/auth/login/?next=/create/')

    def test_create(self):
        """Проверка доступности адреса /create/
        для авторизированного пользователя"""
        responce = self.authorized_client.get('/create/')
        self.assertEqual(responce.reason_phrase, 'OK')

    def test_edit_unlog(self):
        """Проверка перенаправления не авторизированного пользователя
        с /posts/{id}/edit/ на /auth/login/?next=/posts/{id}/edit/"""
        id = StaticURLTests.post.id
        responce = self.guest_client.get(f'/posts/{id}/edit/', follow=True)
        self.assertRedirects(responce, f'/auth/login/?next=/posts/{id}/edit/')

    def test_edit_no_author(self):
        """Проверка перенаправления пользователя, не являющимся автором
        с /posts/{id}/edit/ на /posts/{id}/"""
        id = StaticURLTests.post.id
        responce = self.authorized_client.get(f'/posts/{id}/edit/',
                                              follow=True)
        self.assertRedirects(responce, f'/posts/{id}/')

    def test_edit(self):
        """Проверка доступности адреса /posts/{id}/edit/ для автора"""
        id = StaticURLTests.post.id
        responce = self.authorized_client2.get(f'/posts/{id}/edit/',
                                               follow=True)
        self.assertEqual(responce.reason_phrase, 'OK')

    def test_unexsist(self):
        """Проверка ошибки 404 для несуществующей страницы"""
        responce = self.guest_client.get('/sdfsd/')
        self.assertEqual(responce.reason_phrase, 'Not Found')

    def test_template(self):
        """Адрес из словаря template использует соответсвующий шаблон"""
        cache.clear()
        for url, template in self.templates.items():
            with self.subTest(url=url):
                if url == '/posts/1/edit/' or url == '/create/':
                    response = self.authorized_client2.get(url)
                else:
                    response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_comment_unlog(self):
        """Проверка перенаправления не авторизированного пользователя
        с /posts/{id}/comment/ на /auth/login/?next=/posts/{id}/comment/"""
        id = StaticURLTests.post.id
        responce = self.guest_client.get(f'/posts/{id}/comment/', follow=True)
        self.assertRedirects(responce, f'/auth/login/?next=/posts/{id}/comment/')

    def test_following(self):
        """Проверка подписки авторизованному пользователю"""
        self.authorized_client.get('/profile/auth/follow/')
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=User.objects.get(username='auth')
            ).exists()
        )

    def test_un_following(self):
        """Проверка отписки авторизованному пользователю"""
        self.authorized_client.get('/profile/auth/follow/')
        self.authorized_client.get('/profile/auth/unfollow/')
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=User.objects.get(username='auth')
            ).exists()
        )

    def test_new_post_for_follower(self):
        cache.clear()
        self.authorized_client.get('/profile/auth/follow/')
        new_post = Post.objects.create(
            author=StaticURLTests.user,
            text='Тестовый пост 2'
        )
        response_follow = self.authorized_client.get(
            '/follow/'
        )
        response_un_follow = self.authorized_client2.get(
            '/follow/'
        )
        self.assertTrue(
            new_post in response_follow.context.get('page_obj').object_list
        )
        self.assertFalse(
            new_post in response_un_follow.context.get('page_obj').object_list
        )
        
