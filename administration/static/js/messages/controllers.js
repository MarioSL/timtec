(function(angular){
    'use strict';

    var module = angular.module('messages.controllers', ['ui.tinymce', 'ui.bootstrap']);

    // Service to share data across the controllers
    module.factory('messages_list', function() {
        return {
            messages : []
        };
    });

    module.controller('NewMessageController', ['$scope', '$interval', '$uibModal', '$window', 'Message', 'Student', 'StudentSearch', 'ClassSimple', 'messages_list', '$rootScope',
            function($scope, $interval, $uibModal, $window, Message, Student, StudentSearch, ClassSimple, messages_list, $rootScope) {
                $scope.course_id = parseInt($window.course_id, 10);
                $scope.messages = messages_list.messages;
                $scope.new_message = function () {
                    var modalInstance = $uibModal.open({
                        templateUrl: 'newMessageModal.html',
                        controller: ['$scope', '$uibModalInstance', 'course_id', SendMessageModalInstanceCtrl],
                        resolve: {
                            course_id: function () {
                                return $scope.course_id;
                            }
                        }
                    });
                };
                var SendMessageModalInstanceCtrl = function ($scope, $uibModalInstance, course_id) {

                    $scope.tinymceModel = 'Initial content';
                    $scope.tinymceOptions = {
                        resize: false,
                        menubar:false,
                        statusbar: false,

                        plugins: 'textcolor link',
                        toolbar: "undo redo styleselect bold italic forecolor backcolor link",
                    };

                    $scope.new_message = new Message();
                    $scope.new_message.course = course_id;
                    $scope.new_message.users = [];
                    $scope.recipient_list = [];
                    $scope.empty_msg_subject_error = false;
                    $scope.empty_msg_body_error = false;
                    $scope.sending = false;
                    $scope.progressbar_counter = 0;
                    $scope.specific_classes = [];

                    $scope.classes = ClassSimple.query({course: course_id}, function(classes){
                        classes.checked = [];
                        return classes;
                    });

                    // trick to user modal.all_checked in ng-model html tag
                    $scope.modal = {};
                    $scope.modal.all_checked = true;

                    $scope.send = function () {

                        // progressbar
                        $interval(function(){
                            if($scope.progressbar_counter == 0){
                                $scope.progressbar_counter = 20;
                            }
                            $scope.progressbar_counter++;
                        },1000,0);

                        // TODO validação dos campo: títle e message não podem ser vazios
                        if ($scope.modal.all_checked) {
                            $scope.new_message.users = [];
                            angular.forEach($scope.classes, function(klass) {
                                angular.forEach(klass.students, function(student) {
                                    $scope.new_message.users = $scope.new_message.users.concat(student);
                                });
                            });
                        } else if ($scope.specific_classes.length > 0) {
                            angular.forEach($scope.specific_classes, function(klass) {
                                angular.forEach(klass.students, function(student) {
                                    $scope.new_message.users = $scope.new_message.users.concat(student);
                                });
                            });
                        }
                        if ($scope.new_message.message && $scope.new_message.subject) {
                            $scope.sending = true;
                            $scope.new_message.$save({}, function(new_message){
                                messages_list.messages.unshift(new_message);
                                $scope.progressbar_counter = 100;
                                $rootScope.$broadcast('newMessage');
                                $scope.sending = false;
                                $uibModalInstance.close();
                            });
                            $scope.empty_msg_subject_error = false;
                            $scope.empty_msg_body_error = false;
                        }
                        if (!$scope.new_message.message) {
                            $scope.empty_msg_body_error = true;
                        } else {
                            $scope.empty_msg_body_error = false;
                        }
                        if (!$scope.new_message.subject) {
                            $scope.empty_msg_subject_error = true;
                        } else {
                            $scope.empty_msg_subject_error = false;
                        }
                    };

                    $scope.cancel = function () {
                        $uibModalInstance.dismiss();
                    };
                    $scope.getUsers = function(val) {
                        return new StudentSearch(val, course_id);
                    };

                    $scope.on_select_student = function(model) {
                        $scope.new_message.users.unshift(model.id);
                        $scope.recipient_list.unshift(model);
                        $scope.asyncSelected = '';
                    };

                    $scope.remove_student = function(index) {
                        $scope.new_message.users.splice(index, 1);
                        $scope.recipient_list.splice(index, 1);
                    };

                };
            }
        ]);

    module.controller('MessagesListController', ['$scope', '$uibModal', '$window', 'Message', 'messages_list',
        function($scope, $uibModal, $window, Message, messages_list) {
            $scope.USER_ID = parseInt(window.USER_ID);
            $scope.course_id = parseInt($window.course_id, 10);
            $scope.course_slug = $window.course_slug;
            messages_list.messages = Message.query({course: $scope.course_id});
            $scope.messages = messages_list.messages;
            $scope.$on('newMessage', function() {
                $scope.messages = messages_list.messages;
            });
        }
    ]);

    module.controller('MessageController', ['$scope', '$window', 'Message',
        function($scope, $window, Message) {
            $scope.course_id = parseInt($window.course_id, 10);
            $scope.message_id = document.location.href.match(/message\/([0-9]+)/)[1];
            $scope.message = Message.get({messageId: $scope.message_id}, function(message) {});

            $scope.show_recipients = false;
            $scope.toggle_recipient_list = function(){
                if($scope.show_recipients) {
                    $scope.show_recipients = false;
                } else {
                    $scope.show_recipients = true;
                }
            };
        }
    ]);
})(angular);
