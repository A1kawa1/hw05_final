import shutil
import tempfile
from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from posts.models import Post, Group

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormTest(TestCase):
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
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsFormTest.user)

    def test_form_create_post(self):
        """Валидная форма создает запись в Post"""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        test_form = {
            'text': '123',
            'group': PostsFormTest.group.id,
            'image': uploaded
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=test_form,
            follow=True
        )
        last_post = Post.objects.all().latest('id')
        self.assertEqual(last_post.text, test_form['text'])
        self.assertEqual(last_post.author, PostsFormTest.user)
        self.assertEqual(last_post.group, PostsFormTest.group)
        self.assertEqual(last_post.image, 'posts/small.gif')

    def test_form_edit_post(self):
        """Валидная форма изменяет запись в Post"""
        group = Group.objects.create(
            title='Измененная группа',
            slug='change_slug',
            description='Тестовое описание',
        )
        test_form = {
            'text': 'измененный',
            'group': group.id
        }
        self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostsFormTest.post.id}
            ),
            data=test_form
        )
        new_post = Post.objects.get(id=PostsFormTest.post.id)
        self.assertEqual(new_post.text, test_form['text'])
        self.assertEqual(new_post.group.title, group.title)
        self.assertEqual(new_post.author, PostsFormTest.user)
