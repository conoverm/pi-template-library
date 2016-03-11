'use strict';

/**
 * @ngdoc function
 * @name appApp.controller:MainCtrl
 * @description
 * # MainCtrl
 * Controller of the appApp
 */

angular.module('pintTemplateLibrary')
.controller('MainCtrl', function($scope, $http, $firebaseObject, $firebaseArray) {

  var ref = new Firebase("https://strategytemplates.firebaseio.com");
  // var ref1 = new Firebase("https://strategytemplates.firebaseio.com/3");
  // $scope.selectedTemplate = {}
  // download the data into a local object
  // $scope.data = $firebaseObject(ref1)
  $scope.templates = $firebaseArray(ref)
  

  $scope.templates.$loaded()
    .then(function(x) {
      console.log($scope.templates)
    })
    .catch(function(error) {
      console.log("Error:", error);
    });      

    $scope.showSelected = function(){

      console.log($scope)
      console.log($scope.templates)
      console.log($scope.one)
    }

    $scope.selectTemplate = function(template){
      $scope.selectedTemplate = template
      template.selected = true
      $scope.newStrategies = []
      for (var i = 4; i >= 0; i--) {
      	$scope.newStrategies[i] = angular.copy($scope.selectedTemplate.template)
      	console.log(i)
      	$scope.newStrategies[i].id = i
      	// $scope.newStrategies[i].concepts = [{}]
      	console.log($scope.newStrategies[i])
      };

      console.log($scope.newStrategies)

    }
  


  // $scope.data.$loaded().then(function(data){
  // 	$scope.data.audience = 654322
  //   $scope.data.editable = 'concepts, audience, budget'
  //   $scope.data.template = {

  //     'bid_aggressiveness': "53.00",
  //     'bid_price_is_media_only': true,
  //     'budget': 1000000,
  //     'campaign_id': 12345,
  //     'effective_goal_value': 11.15,
  //     'frequency_amount': 1,
  //     'frequency_interval': "day",
  //     'frequency_type': "asap",
  //     'goal_type': "spend",
  //     'goal_value': 12.25,
  //     'max_bid': 3.00,
  //     'media_type': "DISPLAY",
  //     'pacing_amount': 200,
  //     'pacing_interval': "day",
  //     'pacing_type': "even",   
  //     'run_on_all_exchanges': true,
  //     'run_on_all_pmp': false,
  //     'run_on_display': true,
  //     'run_on_mobile': true,
  //     'run_on_streaming': false,
  //     'site_restriction_transparent_urls': false,
  //     'site_selectiveness': "REDUCED",
  //     'supply_type': "RTB",
  //     'type': "AUD",
  //     'use_campaign_end': true,
  //     'use_campaign_start': true,
  //     'use_mm_freq': false,
  //     'use_optimization': true            
  //   }

  //   $scope.data.name = 'Live Nation Artist REM'

  //   $scope.data.$save().then(function(ref) {
  //     ref.key() === $scope.data.$id; // true
  //   }, function(error) {
  //     console.log("Error:", error);
  //   });

  // })

  var t1endpoint = 'https://t1qa1.mediamath.com/api/v2.0/';

  /*
   ok here's the session nonsense to skip a log in screen.
   Log into t1qa1.mediamath.com and open this project under SOMETHING.mediamath.com (the hosts
   file hack we all use).

   Serve this project. I just use `serve`. (npm install -g serve, https://www.npmjs.com/package/serve) 

   Open the url to this served project: it will be SOMETHING.mediamath.com:3000

   The cookie you got by logging into t1qa1 will be in your browser and will be sent to adama
   because of the magic header `withCredentials: true`.
   */
  
  var session = $http.get('https://t1qa1.mediamath.com/api/v2.0/session', { withCredentials: true})
  .then(function(response){
    console.info(response);
    // hey leif
    // cookie = response.data.session.sessionid
  });

  $scope.data = $firebaseObject(ref);
  $scope.clone = {};

  $scope.saveStrategies = function(){

  	for (var i = $scope.newStrategies.length - 1; i >= 0; i--) {
  		$scope.newStrategies[i].name = $scope.selectedTemplate.name + '_' + $scope.newStrategies[i].pixel_target_expr
  		console.log($scope.newStrategies[i])
  	};

  }

  $scope.getLocation = function(val) {
    console.info('getlocation', val)
    return $http({
      method: 'get',
      url: t1endpoint + 'target_values?dimension=REGN&sort_by=name',
      params: {
        order_by: 'descending',
        page_limit: '20',
        q: 'name=:' + val + '*'
      },
      withCredentials: true
    }).then(function(response){
      
      if (response.status !== 200){
        $scope.errorMessage = 'No targets found. Please try again later.';
        $scope.showErrorMessage = true;
        $timeout(function(){
          $scope.showErrorMessage = null;
        }, 10000);
      } else {
        console.info(res)
        var res = response.data.entities.entity;
        if(res.length === 0){
          //skip displaying the error message for IDs, since they are not auto suggested.
          if(queryTerm[0] != '#'){
            $scope.errorMessage = 'No targets found. Please try again later.';
            $scope.showErrorMessage = true;
          }
        } else{
          var targets = [];
          angular.forEach(res, function(item) {
            var obj = {
              'id': item.id,
              'name': item.name,
              'displayName': item.name + ' - ' + item.id
            };
            targets.push(obj);
          });
          return targets;
        }
      }
    });
  };
});
