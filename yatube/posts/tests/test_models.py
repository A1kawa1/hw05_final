from django.test import TestCase
from django.contrib.auth import get_user_model
from posts.models import Post, Group


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User = get_user_model()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_str(self):
        """Проверка вывода поля text при использовании как строки"""
        expected = PostModelTest.post.text[:15]
        self.assertEqual(str(PostModelTest.post), expected)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым"""
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа'
        }

        for field, expected in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    PostModelTest.post._meta.get_field(field).verbose_name,
                    expected)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым"""
        field_verboses = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост'
        }

        for field, expected in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    PostModelTest.post._meta.get_field(field).help_text,
                    expected)


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='new group'
        )

    def test_str(self):
        """Проверка вывода поля text при использовании как строки"""
        expected = GroupModelTest.group.title
        self.assertEqual(str(GroupModelTest.group), expected)
