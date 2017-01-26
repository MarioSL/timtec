from django.contrib.flatpages.models import FlatPage
from django.contrib.auth import get_user_model
from core.models import (Course, CourseProfessor, CourseStudent, Lesson,
                         Video, StudentProgress, Unit, ProfessorMessage,
                         Class, CourseAuthor, CourseCertification,
                         CertificationProcess, Evaluation, CertificateTemplate,
                         IfCertificateTemplate)
from accounts.serializers import (TimtecUserSerializer,
                                  TimtecUserAdminCertificateSerializer, TimtecUserAdminSerializer)
from activities.models import Activity
from activities.serializers import ActivitySerializer
from notes.models import Note
from rest_framework import serializers
from accounts.models import UserSocialAccount


class ProfessorMessageSerializer(serializers.ModelSerializer):

    professor = TimtecUserSerializer(read_only=True)
    users_details = TimtecUserSerializer(many=True, source='users', read_only=True)

    class Meta:
        model = ProfessorMessage
        fields = ('id', 'users', 'users_details', 'users_that_read', 'course', 'subject', 'message', 'date', 'professor')


class UserMessageSerializer(serializers.ModelSerializer):

    course = serializers.CharField(source='course.name')
    professor = serializers.CharField(source='professor.get_full_name')
    is_read = serializers.SerializerMethodField()
    subject = serializers.SerializerMethodField()

    class Meta:
        model = ProfessorMessage
        read_only_fields = fields = ('id', 'course', 'subject', 'date', 'professor', 'is_read', 'get_absolute_url')

    def get_is_read(self, obj):
        current_user = self.context.get("request").user
        if obj.users_that_read.filter(id=current_user.id):
            return True
        return False

    def get_subject(self, obj):
        from django.utils.text import Truncator
        return Truncator(obj.subject).chars(45)


class ProfessorMessageUserDetailsSerializer(serializers.ModelSerializer):

    professor = TimtecUserSerializer(read_only=True)
    users_details = TimtecUserAdminSerializer(many=True, source='users', read_only=True)
    users_that_read_details = TimtecUserSerializer(many=True, source='users_that_read', read_only=True)
    users_that_not_read_details = TimtecUserSerializer(many=True, source='users_that_not_read', read_only=True)

    class Meta:
        model = ProfessorMessage
        fields = ('id', 'course', 'users', 'users_details', 'users_that_read', 'users_that_read_details',
                  'subject', 'users_that_not_read_details', 'message', 'date', 'professor')


class BaseCourseSerializer(serializers.ModelSerializer):
    professors = serializers.SerializerMethodField('get_professor_name')
    home_thumbnail_url = serializers.SerializerMethodField()
    is_assistant_or_coordinator = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ("id", "slug", "name", "status", "home_thumbnail_url",
                  "start_date", "home_published", "has_started",
                  "min_percent_to_complete", "professors", "is_assistant_or_coordinator",)

    @staticmethod
    def get_professor_name(obj):
        if obj.course_authors.all():
            return [author.get_name() for author in obj.course_authors.all()]
        return ''

    @staticmethod
    def get_home_thumbnail_url(obj):
        if obj.home_thumbnail:
            return obj.home_thumbnail.url
        return ''

    def get_is_assistant_or_coordinator(self, obj):
        if self.context:
            return obj.is_assistant_or_coordinator(self.context['request'].user)


class BaseClassSerializer(serializers.ModelSerializer):

    class Meta:
        model = Class
        fields = ("id", "name", "assistants", "user_can_certificate")


class BaseEvaluationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Evaluation


class BaseCertificationProcessSerializer(serializers.ModelSerializer):
    evaluation = BaseEvaluationSerializer()

    class Meta:
        model = CertificationProcess


class BaseCourseCertificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = CourseCertification


class CertificationProcessSerializer(serializers.ModelSerializer):
    course_certification = serializers.SlugRelatedField(slug_field="link_hash", read_only=True)

    class Meta:
        model = CertificationProcess


class CourseCertificationSerializer(serializers.ModelSerializer):
    processes = BaseCertificationProcessSerializer(many=True, read_only=True)
    approved = BaseCertificationProcessSerializer(source='get_approved_process', read_only=True)
    course = serializers.SerializerMethodField()
    url = serializers.ReadOnlyField(source='get_absolute_url')

    class Meta:
        model = CourseCertification
        fields = ('link_hash', 'created_date', 'is_valid', 'processes', 'type',
                  'approved', 'course', 'url')

    @staticmethod
    def get_course(obj):
        return obj.course.id


class ProfileCourseCertificationSerializer(serializers.ModelSerializer):
    course = BaseCourseSerializer()
    approved = BaseCertificationProcessSerializer(source='get_approved_process')

    class Meta:
        model = CourseCertification
        fields = ('link_hash', 'created_date', 'is_valid', 'processes', 'type',
                  'approved', 'course')


class EvaluationSerializer(serializers.ModelSerializer):
    processes = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Evaluation


class CertificateTemplateSerializer(serializers.ModelSerializer):

    class Meta:
        model = CertificateTemplate
        fields = ('id', 'course', 'organization_name', 'base_logo_url', 'cert_logo_url', 'role', 'name', 'signature_url', )


class IfCertificateTemplateSerializer(CertificateTemplateSerializer):

    class Meta:
        model = IfCertificateTemplate
        fields = ('id', 'course', 'organization_name', 'base_logo_url', 'cert_logo_url',
                  'pronatec_logo', 'mec_logo', 'role', 'name', 'signature_url',)


class CertificateTemplateImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = CertificateTemplate
        fields = ('base_logo', 'cert_logo', 'signature', )


class ClassActivitySerializer(serializers.ModelSerializer):
    activity_answers = serializers.SerializerMethodField()

    class Meta:
        model = Class
        fields = ['id', 'name', 'activity_answers', 'course']

    def get_activity_answers(self, obj):
        request = self.context.get("request")
        activity_id = request.query_params.get('activity', None)

        try:
            queryset = Answer.objects.filter(
                activity=activity_id,
                activity__unit__lesson__course=obj.course,
                user__in=obj.students.all()
            ).exclude(user=request.user)
        except Answer.DoesNotExist:
            return

        return AnswerSerializer(
            queryset, many=True, **{'context': self.context}).data


class VideoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Video
        fields = ('id', 'name', 'youtube_id',)


class CourseSerializer(serializers.ModelSerializer):
    # BUGFIX: intro_video needs to be read_only=False. This is a little workaround to make other modules work
    intro_video = VideoSerializer(required=False, read_only=True)
    thumbnail_url = serializers.ReadOnlyField(source='get_thumbnail_url')

    has_started = serializers.ReadOnlyField()
    professors = TimtecUserSerializer(source='authors', many=True, read_only=True)
    home_thumbnail_url = serializers.SerializerMethodField()
    professors = TimtecUserSerializer(read_only=True, many=True)
    is_user_assistant = serializers.SerializerMethodField()
    is_user_coordinator = serializers.SerializerMethodField()
    is_assistant_or_coordinator = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ("id", "slug", "name", "intro_video", "application", "requirement",
                  "abstract", "structure", "workload", "pronatec", "status",
                  "thumbnail_url", "home_thumbnail_url", "home_position",
                  "start_date", "home_published", "authors_names", "has_started",
                  "min_percent_to_complete", "is_user_assistant", "is_user_coordinator",
                  "professors", "is_assistant_or_coordinator", "welcome_email")

    @staticmethod
    def get_professor_name(obj):
        if obj.course_authors.all():
            return [author.get_name() for author in obj.course_authors.all()]
        return ''

    @staticmethod
    def get_professors_names(obj):
        professors = obj.get_video_professors()
        if professors:
            if len(professors) > 1:
                return '{0} e {1}'.format(professors[0].user, professors[1].user)
            else:
                return professors[0].user
        return ''

    @staticmethod
    def get_home_thumbnail_url(obj):
        if obj.home_thumbnail:
            return obj.home_thumbnail.url
        return ''

    def get_is_user_assistant(self, obj):
        return obj.is_course_assistant(self.context['request'].user)

    def get_is_user_coordinator(self, obj):
        return obj.is_course_coordinator(self.context['request'].user)

    def get_is_assistant_or_coordinator(self, obj):
        return obj.is_assistant_or_coordinator(self.context['request'].user)


class CourseStudentSerializer(serializers.ModelSerializer):
    user = TimtecUserSerializer(read_only=True)
    course_finished = serializers.BooleanField()
    can_emmit_receipt = serializers.BooleanField()
    percent_progress = serializers.IntegerField()
    min_percent_to_complete = serializers.IntegerField()

    current_class = BaseClassSerializer(source='get_current_class')
    course = BaseCourseSerializer()
    certificate = CourseCertificationSerializer()

    class Meta:
        model = CourseStudent
        fields = ('id', 'user', 'course', 'course_finished',
                  'certificate', 'can_emmit_receipt', 'percent_progress',
                  'current_class', 'min_percent_to_complete',)


class CourseStudentClassSerializer(CourseStudentSerializer):

    user = TimtecUserAdminCertificateSerializer(read_only=True)

    class Meta:
        model = CourseStudent
        fields = ('id', 'user', 'course_finished', 'start_date',
                  'certificate', 'can_emmit_receipt', 'percent_progress',)


class ClassSerializer(serializers.ModelSerializer):
    students_details = CourseStudentClassSerializer(source='get_students', many=True, read_only=True)
    processes = CertificationProcessSerializer(read_only=True, many=True)
    evaluations = EvaluationSerializer(read_only=True, many=True)
    course = CourseSerializer(read_only=True)
    assistants = TimtecUserSerializer(read_only=True, many=True)

    class Meta:
        model = Class


class ClassSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ('id', 'name', 'course', 'students')

    def update(self, instance, validated_data, **kwargs):
        assistants = self.context['request'].data.get('assistants', None)
        updated_class = super(ClassSerializer, self).update(instance, validated_data)
        # If there are assistans to be associated with the class, do it now
        for assistant in assistants:
            updated_class.assistants.add(assistant['id'])
        return updated_class


class UserSocialAccountSerializer(serializers.ModelSerializer):

    get_absolute_url = serializers.ReadOnlyField()

    class Meta:
        model = UserSocialAccount
        fields = ('social_media', 'nickname', 'get_absolute_url')


class ProfileSerializer(TimtecUserSerializer):

    certificates = ProfileCourseCertificationSerializer(many=True, source="get_certificates")
    social_medias = UserSocialAccountSerializer(many=True, source='get_social_media')
    courses = BaseCourseSerializer(many=True, source='get_current_courses')

    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'name', 'first_name', 'last_name',
                  'biography', 'picture', 'is_profile_filled', 'occupation', 'birth_date',
                  'certificates', 'city', 'state', 'site', 'occupation', 'social_medias', 'courses')


class CourseThumbSerializer(serializers.ModelSerializer):

    class Meta:
        model = Course
        fields = ("id", "thumbnail", "home_thumbnail")


class StudentProgressSerializer(serializers.ModelSerializer):
    complete = serializers.DateTimeField(required=False)
    user = TimtecUserSerializer(read_only=True, required=False)

    class Meta:
        model = StudentProgress
        fields = ('unit', 'complete', 'user',)


class UnitSerializer(serializers.ModelSerializer):
    video = VideoSerializer(required=False, allow_null=True)
    activities = ActivitySerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Unit
        fields = ('id', 'title', 'video', 'activities', 'side_notes', 'position',)


class LessonSerializer(serializers.ModelSerializer):

    units = UnitSerializer(many=True)
    is_course_last_lesson = serializers.BooleanField(read_only=True)

    class Meta:
        model = Lesson
        fields = ('id', 'course', 'is_course_last_lesson', 'desc',
                  'name', 'notes', 'position', 'slug', 'status', 'units',
                  'thumbnail')

    def update(self, instance, validated_data):

        units = self.update_units(self.initial_data.get('units'), instance)

        for old_unit in instance.units.all():
            if old_unit not in units:
                old_unit.delete()
            else:
                new_activities = units[units.index(old_unit)].activities
                if old_unit.activities != new_activities:
                    for activity in old_unit.activities:
                        if activity not in new_activities:
                            activity.delete()

        validated_data.pop('units')
        return super(LessonSerializer, self).update(instance, validated_data)

    def create(self, validated_data):
        units_data = validated_data.pop('units')
        new_lesson = super(LessonSerializer, self).create(validated_data)
        # units_data = self.initial_data.get('units')

        self.update_units(units_data, new_lesson)

        return new_lesson

    @classmethod
    def update_units(cls, units_data, lesson):
        units = []
        for unit_data in units_data:
            activities_data = unit_data.pop('activities')
            unit_data.pop('lesson', None)

            video_data = unit_data.pop('video', None)
            if video_data:
                video = Video(**video_data)
                video.save()
            else:
                video = None
            unit = Unit(lesson=lesson, video=video, **unit_data)
            unit.save()
            activities = []
            for activity_data in activities_data:
                # import pdb;pdb.set_trace()
                activity_id = activity_data.pop('id', None)
                activity, _ = Activity.objects.get_or_create(id=activity_id)
                activity.comment = activity_data.get('comment', None)
                activity.data = activity_data.get('data', None)
                activity.expected = activity_data.get('expected', None)
                activity.type = activity_data.get('type', None)
                activity.unit = unit
                activity.save()
                activities.append(activity)
            unit.activities = activities
            units.append(unit)
        return units


class NoteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Note
        fields = ('id', 'text', 'content_type', 'object_id',)


class UnitNoteSerializer(serializers.ModelSerializer):

    user_note = NoteSerializer()

    class Meta:
        model = Unit
        fields = ('id', 'title', 'video', 'position', 'user_note')
        # fields = ('id', 'title', 'video', 'position')


class LessonNoteSerializer(serializers.ModelSerializer):

    units_notes = UnitNoteSerializer(many=True)
    course = serializers.SlugRelatedField(slug_field='slug', read_only=True)

    class Meta:
        model = Lesson
        fields = ('id', 'name', 'position', 'slug', 'course', 'units_notes',)
        # fields = ('id', 'name', 'position', 'slug', 'course',)


class CourseNoteSerializer(serializers.ModelSerializer):

    lessons_notes = LessonNoteSerializer(many=True)
    course_notes_number = serializers.IntegerField(required=False)

    class Meta:
        model = Course
        fields = ('id', 'slug', 'name', 'lessons_notes', 'course_notes_number',)


class CourseProfessorSerializer(serializers.ModelSerializer):

    user = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.all(), required=False)
    user_info = TimtecUserSerializer(source='user', read_only=True)
    course_info = CourseSerializer(source='course', read_only=True)
    get_name = serializers.CharField(read_only=True)
    get_biography = serializers.CharField(read_only=True)
    get_picture_url = serializers.CharField(read_only=True)
    current_user_classes = ClassSerializer(source='get_current_user_classes', read_only=True, many=True)

    class Meta:
        fields = ('id', 'course', 'course_info', 'user', 'name', 'biography', 'picture', 'user_info',
                  'get_name', 'get_biography', 'get_picture_url', 'role', 'current_user_classes',
                  'is_course_author',)
        model = CourseProfessor


class CourseAuthorSerializer(serializers.ModelSerializer):
    user_info = TimtecUserSerializer(source='user', read_only=True)
    course_info = CourseSerializer(source='course', read_only=True)
    get_name = serializers.ReadOnlyField()
    get_biography = serializers.ReadOnlyField()
    get_picture_url = serializers.ReadOnlyField()

    class Meta:
        fields = ('id', 'course', 'course_info', 'user', 'name', 'biography', 'picture', 'user_info',
                  'get_name', 'get_biography', 'get_picture_url', 'position')
        model = CourseAuthor


class CourseAuthorPictureSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('id', 'picture',)
        model = CourseAuthor


class FlatpageSerializer(serializers.ModelSerializer):

    class Meta:
        model = FlatPage
        exclude = ('sites', )
