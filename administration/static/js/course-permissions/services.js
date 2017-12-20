(function(angular) {
	'use strict';
	var app = angular.module('course-permissions.services', ['ngResource']);

    app.factory('Groups', function($resource) {
		return $resource('/api/group/:groupId', {}, {
		});
	});

})(window.angular);