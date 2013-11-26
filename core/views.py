# -*- coding: utf-8 -*-
import json

from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import DetailView
from django.views.generic.base import RedirectView, View, TemplateView
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from braces.views import LoginRequiredMixin

from .serializers import CourseSerializer, AnswerSerializer, LessonSerializer, StudentProgressSerializer
from .models import Course, Answer, Lesson, StudentProgress, Unit

from forms import ContactForm


class HomeView(View):
    def get(self, request):
        latest = Course.objects.latest('publication')
        return redirect(reverse('course_intro', args=[latest.slug]))


class ContactView(View):
    def post(self, request):
        status_code = 200
        contact_form = ContactForm(request.POST)

        if contact_form.is_valid():
            contact_form.send_email()
            content = json.dumps([])
        else:
            status_code = 400
            content = json.dumps(contact_form.errors)

        response = self.options(request)
        response['Content-Type'] = 'application/json'
        response['Content-Length'] = len(content)
        response.content = content
        response.status_code = status_code

        return response


class CourseView(DetailView):
    model = Course
    template_name = 'course.html'

    def get_context_data(self, **kwargs):
        context = super(CourseView, self).get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated():
            units_done = StudentProgress.objects.filter(user=user, unit__lesson__course=self.object)\
                                                .exclude(complete=None)\
                                                .values_list('unit', flat=True)
            context['units_done'] = units_done

            user_is_enrolled = self.object.students.filter(id=user.id).exists()
            context['user_is_enrolled'] = user_is_enrolled

        return context


class UserCoursesView(LoginRequiredMixin, TemplateView):
    template_name = 'user-courses.html'


class EnrollCourseView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_object(self):
        if hasattr(self, 'object'):
            return self.object
        self.object = Course.objects.get(**self.kwargs)
        return self.object

    def get_redirect_url(self, **kwargs):
        course = self.get_object()
        course.enroll_student(self.request.user)
        return reverse('lesson', args=[course.first_lesson().slug])


class CourseViewSet(viewsets.ModelViewSet):
    model = Course
    lookup_field = 'slug'
    serializer_class = CourseSerializer

    def post(self, request, **kwargs):
        course = self.get_object()
        serializer = CourseSerializer(course, request.DATA)

        if serializer.is_valid():
            serializer.save()
            return Response(status=200)
        else:
            return Response(serializer.errors, status=403)


class LessonDetailView(LoginRequiredMixin, DetailView):
    model = Lesson
    template_name = "lesson.html"


class LessonViewSet(viewsets.ModelViewSet):
    model = Lesson
    serializer_class = LessonSerializer
    filter_fields = ('course__slug',)

    def get_queryset(self):
        queryset = super(LessonViewSet, self).get_queryset()
        if self.request.user.is_active:
            return queryset
        return queryset.filter(published=True)


class StudentProgressViewSet(viewsets.ModelViewSet):
    model = StudentProgress
    serializer_class = StudentProgressSerializer
    filter_fields = ('unit__lesson',)

    def pre_save(self, obj):
        obj.user = self.request.user
        return super(StudentProgressViewSet, self).pre_save(obj)

    def get_queryset(self):
        user = self.request.user
        return StudentProgress.objects.filter(user=user)


class UpdateStudentProgressView(APIView):
    model = StudentProgress

    def post(self, request, unitId=None):
        user = request.user

        try:
            unit = Unit.objects.get(id=unitId)
        except Unit.DoesNotExist as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        response = {}
        if not unit.activity:
            progress, created = StudentProgress.objects.get_or_create(user=user, unit=unit)
            progress.complete = timezone.now()
            progress.save()
            response['msg'] = 'Unit completed.'
            response['complete'] = progress.complete
        return Response(response, status=status.HTTP_201_CREATED)


class AnswerViewSet(viewsets.ModelViewSet):
    model = Answer
    serializer_class = AnswerSerializer
    filter_fields = ('activity', 'user',)

    def pre_save(self, obj):
        obj.user = self.request.user

    def post_save(self, obj, **kwargs):
        unit = self.request.DATA.get('unit', None)
        user = self.request.user
        progress, created = StudentProgress.objects.get_or_create(user=user, unit_id=unit)

        if obj.is_correct():
            progress.complete = timezone.now()
        progress.save()

    def get_queryset(self):
        return Answer.objects.filter(user=self.request.user)
