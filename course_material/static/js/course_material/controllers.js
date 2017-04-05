(function (angular) {
    'use strict';

    var app = angular.module('courseMaterial.controllers', ['ngCookies']);

    app.controller('CourseMaterialEditorCtrl', ['$scope', '$window', '$sce', 'CourseMaterial','CourseMaterialFile',
        function ($scope, $window, $sce, CourseMaterial, CourseMaterialFile) {
            $scope.courseId = $window.course_id;

            // Set buttons for the tinyMCE editor
            $scope.tinymceOptions = {
              toolbar: 'bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | quicklink link fullscreen | removeformat'
            };

            $scope.course_materials = CourseMaterial.query({course__id: $scope.courseId}, function (course_materials){
                if(course_materials.length === 1) {
                    $scope.course_material = course_materials[0];
                }
            });

            $scope.save_course_material = function(){
                $scope.course_material.$update({course: $scope.courseId}, function(){
                    $scope.alert.success('Alterações salvas com sucesso!');
                    $scope.editando = false;
                });
            };

            $scope.delete_file = function(file_obj){
                if (confirm('Tem certeza que dejeja apagar este arquivo?')){
                    CourseMaterialFile.delete({id: file_obj.id}, function(){
                        angular.forEach($scope.course_material.files, function(file, index){
                            if (file.id == file_obj.id){
                                $scope.course_material.files.splice(index, 1);
                                $scope.alert.success('Arquivo removido com sucesso!');
                            }
                        });
                    });
                }
            };

            $scope.get_as_safe_html = function(html_content) {
                return $sce.trustAsHtml(html_content);
            };
    }]);
})(angular);
