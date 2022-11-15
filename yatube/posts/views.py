from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from posts.models import Post, Group, Comment, Follow, get_user_model
from posts.forms import PostForm, CommentForm
from yatube.settings import QUANTITY_POST

User = get_user_model()


def paginator(post_list, request):
    paginator = Paginator(post_list, QUANTITY_POST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


@cache_page(timeout=20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.select_related('author',
                                            'group')
    context = {
        'page_obj': paginator(post_list, request)
    }

    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    context = {
        'group': group,
        'page_obj': paginator(post_list, request)
    }

    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    if request.user.is_authenticated:
        tmp = Follow.objects.filter(
            user=request.user,
            author=User.objects.get(username=username)
        ).exists()
    else:
        tmp = 0
    post_list = author.posts.all()
    following = 1 if (tmp) else 0
    context = {
        'author': author,
        'page_obj': paginator(post_list, request),
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post=post)[::-1]
    context = {
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if form.is_valid():
        form.instance.author = request.user
        form.save()
        return redirect('posts:profile', username=request.user.username)

    context = {
        'form': form,
    }

    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.instance.author = request.user
        form.save()
        return redirect('posts:post_detail', post_id=post_id)

    context = {
        'form': form,
        'is_edit': True,
    }

    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = Post.objects.get(id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        form.instance.author = request.user
        form.instance.post = post
        form.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    user = request.user
    following = Follow.objects.filter(user=user)
    # get_author = lambda user_author: user_author.author

    def get_author(user_author):
        return user_author.author

    all_following = list(map(get_author, following))
    post_list = Post.objects.select_related(
        'author',
        'group'
    ).filter(author__in=all_following)
    context = {
        'page_obj': paginator(post_list, request)
    }

    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    if request.user == get_object_or_404(User, username=username):
        return redirect('posts:profile', username=username)

    Follow.objects.create(
        user=request.user,
        author=get_object_or_404(User, username=username)
    )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    Follow.objects.get(
        user=request.user,
        author=get_object_or_404(User, username=username)
    ).delete()
    return redirect('posts:profile', username=username)
