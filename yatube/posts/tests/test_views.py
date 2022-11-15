import shutil
import tempfile
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from posts.models import Post, Group

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post_list = [Post(author=cls.user,
                              text='Тестовый пост',
                              group=cls.group,
                              image=cls.uploaded)] * 13
        Post.objects.bulk_create(cls.post_list)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsViewsTest.user)
        self.template = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group',
                    kwargs={'slug': 'test_slug'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'auth'}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': '1'}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': '1'}): 'posts/create_post.html'
        }

    def test_template(self):
        """Адрес из словаря template использует соответсвующий шаблон"""
        cache.clear()
        for reverse_name, template in self.template.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_context_index(self):
        """Шаблон index сформирован с правильным контекстом"""
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIsInstance(response.context.get('page_obj').object_list,
                              list)
        self.assertEqual(response.context['page_obj'][0].image,
                         PostsViewsTest.post_list[0].image)

    def test_cahe_index(self):
        """Проверка кэширования для index """
        response1 = self.authorized_client.get(reverse('posts:index'))
        Post.objects.all().delete()
        response2 = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response1.content,
                         response2.content)
        cache.clear()
        Post.objects.create(
            author=PostsViewsTest.user,
            text='Тестовый пост'
        )
        response3 = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response2.content,
                            response3.content)

    def test_paginator_index(self):
        """В шаблоне index используется paginator"""
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_context_group_list(self):
        """Шаблон group_list сформирован с правильным контекстом"""
        cache.clear()
        response = (self.authorized_client.
                    get(reverse('posts:group',
                                kwargs={'slug': 'test_slug'})))
        posts = response.context.get('page_obj').object_list
        for post in posts:
            self.assertEqual(post.group, PostsViewsTest.group)

        self.assertEqual(response.context['page_obj'][0].image,
                         PostsViewsTest.post_list[0].image)

    def test_paginator_group_list(self):
        """В шаблоне group_list используется paginator"""
        cache.clear()
        response = self.client.get(reverse('posts:group',
                                           kwargs={'slug': 'test_slug'}))
        self.assertEqual(len(response.context['page_obj']), 10)
        response = self.client.get(reverse('posts:group',
                                           kwargs={'slug': 'test_slug'})
                                   + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_context_profile(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = (self.authorized_client.
                    get(reverse('posts:profile',
                                kwargs={'username': 'auth'})))
        posts = response.context.get('page_obj').object_list
        for post in posts:
            self.assertEqual(post.author, PostsViewsTest.user)

        self.assertEqual(response.context['page_obj'][0].image,
                         PostsViewsTest.post_list[0].image)

    def test_paginator_profile(self):
        """В шаблоне profile используется paginator"""
        response = self.client.get(reverse('posts:profile',
                                           kwargs={'username': 'auth'}))
        self.assertEqual(len(response.context['page_obj']), 10)
        response = self.client.get(reverse('posts:profile',
                                           kwargs={'username': 'auth'})
                                   + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_context_post_detail(self):
        """Шаблон post_detail сформирован с правильным контекстом"""
        test_form = {
            'text': '123'
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': '1'}),
            data=test_form
        )
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        )
        self.assertEqual(response.context.get('comments')[0].text,
                         test_form['text'])
        self.assertNotIsInstance(response.context.get('post'), list)
        self.assertEqual(response.context.get('post').id, 1)
        self.assertEqual(response.context.get('post').image,
                         PostsViewsTest.post_list[0].image)

    def test_context_post_detail_unlog(self):
        """Шаблон post_detail сформирован с правильным контекстом
        для неавторизованного пользователя"""
        test_form = {
            'text': '123'
        }
        responce = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': '1'}),
            data=test_form
        )
        self.assertEqual(responce.reason_phrase, 'Found')

    def test_context_create_post(self):
        """Шаблон create_post сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        test_form = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in test_form.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_context_edit_post(self):
        """Шаблон edit_post сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse('posts:post_edit',
                                                      kwargs={'post_id': '1'}))
        test_form = {
            'text': (forms.fields.CharField, 'Тестовый пост'),
            'group': (forms.fields.ChoiceField, 1)
        }
        for value, expected in test_form.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected[0])
                self.assertEqual(response.context.get('form').initial[value],
                                 expected[1])
