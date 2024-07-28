from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework import viewsets, status
from .models import Comment,Post,Topic,PostAttachment
from ..activity.models import Activity
from .serializers import TopicSerializer,PostSerializer,CommentSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.contenttypes.models import ContentType
from .permissions import IsOwner


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_activity(request):#this is to manage the following/unfollowing of topics and also the liking/unliking of posts and comments
    user = request.user
    object_id = request.data.get('object_id')
    object_type = request.data.get('object_type')
    print("hellow")
    if object_type =="topic":
        activity_type=Activity.FOLLOW
    else:
        activity_type=Activity.LIKE
    

    try:
        content_type = ContentType.objects.get(model=object_type)
        model_class = content_type.model_class()
        obj = model_class.objects.get(id=object_id)
    except ContentType.DoesNotExist:
        return Response({"error": "Invalid object type"}, status=status.HTTP_400_BAD_REQUEST)
    except model_class.DoesNotExist:
        return Response({"error": f"{object_type.capitalize()} not found"}, status=status.HTTP_404_NOT_FOUND)

    if Activity.objects.filter(user=user, content_type=content_type, object_id=obj.id,activity_type=activity_type).exists():
        
        Activity.objects.filter(user=user, content_type=content_type, object_id=obj.id,activity_type=activity_type).delete()
        if activity_type=="L":
            response="You have unliked this Item"
        else:
            response="You have unfollowed this Topic"
        return Response({"message": response}, status=status.HTTP_200_OK)

    Activity.objects.create(user=user, content_type=content_type, object_id=obj.id,activity_type=activity_type)
    if activity_type=="L":
        response="You have liked this Item"
    else:
        response="You have followed this Topic"
    return Response({"message":response}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def view_feed(request):
    user = request.user
    activities=Activity.objects.filter(user=user,activity_type=Activity.FOLLOW)
    topic_ids=[]
    for activity in activities:
        topic_ids.append(activity.object_id)
    post=Post.objects.filter(topic__id__in=topic_ids)
    serializer=PostSerializer(post,many=True)
    return Response(serializer.data)

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def get_comments(request, post_id):
#     try:
#         post = Post.objects.get(id=post_id)
#     except Post.DoesNotExist:
#         return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

#     comments = Comment.objects.filter(post=post)
#     return Response(CommentSerializer(comments, many=True).data, status=status.HTTP_200_OK)

class TopicViewSet(viewsets.ModelViewSet):
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(host=self.request.user)

    @action(detail=False, methods=['get'], url_path='view_topics')
    def view_all_topics(self, request, pk=None):

        topics=Topic.objects.all()
        data=TopicSerializer(topics,many=True).data
        return Response(data, status=status.HTTP_200_OK)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(host=self.request.user)

    @action(detail=False, methods=['post'], url_path='post_comment')
    def post_comment(self, request, pk=None):
        user = request.user
        post_id = request.data.get('post_id')
        content = request.data.get('content')
        parent_id = request.data.get('parent_id', None)

        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

        parent_comment = None
        if parent_id:
            try:
                parent_comment = Comment.objects.get(id=parent_id)
            except Comment.DoesNotExist:
                return Response({"error": "Parent comment not found"}, status=status.HTTP_404_NOT_FOUND)

        comment = Comment.objects.create(user=user, post=post, content=content, parent=parent_comment)
        return Response({"message": "Successfully added comment", "comment": CommentSerializer(comment).data}, status=status.HTTP_201_CREATED)


    def get_queryset(self):
        print(self.request.data["is_owner"])
        if (self.request.data["is_owner"]):
            return Comment.objects.filter(user=self.request.user)
        else:
            print("Inside esle")
            return Comment.objects.all()
   

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated,IsOwner]

    def perform_create(self, serializer):
        post=serializer.save(user=self.request.user)
        files = self.request.FILES.getlist('files')
        for file in files:
            try:
                PostAttachment.objects.create(post=post, attachment=file)
            except Exception as e:
                print(e)

    
    def get_queryset(self):
        print(self.request.data["is_owner"])
        if (self.request.data["is_owner"]):
            return Post.objects.filter(user=self.request.user)
        else:
            print("Inside esle")
            return Post.objects.all()

 