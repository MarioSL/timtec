(function(angular){
    'use strict';

    angular.module('messages', [
        'messages.controllers',
        'messages.services',
        'django',
        'timtec-models',
        'ui.bootstrap',
        'checklist-model',
        'markdown',
        'truncate',
        'ngRoute',
        'header',
    ]);
})(angular);
