
//create new strategy
function Strategy(options) {
    this.properties = {}
    this.properties.pixel_target_expr = {}
    this.properties.pixel_target_expr.exclude = {}
    this.properties.pixel_target_expr.include = {}
    this.properties.start_date = options.start_date || Date.now()+3600
    this.properties.end_date = options.stat_date || Date.now()+36000
    this.properties.description = options.description || ""
    this.properties.use_campaign_start = options.use_campaign_start || 1
    this.properties.use_campaign_end = options.use_campaign_end || 1
    this.properties.pixel_target_expr.exclude.operator = ""
    this.properties.pixel_target_expr.exclude.pixels = []
    this.properties.pixel_target_expr.include.operator = ""
    this.properties.pixel_target_expr.include.pixels = ""
    this.properties.budget = options.budget || 0
    this.properties.campaign_id = options.campaign_id
    this.properties.frequency_type = options.frequency_type || ""
    this.properties.goal_type = options.goal_type || ""
    this.properties.goal_value = options.goal_value || ""
    this.properties.max_bid = options.max_bid || ""
    this.properties.name = options.name || "My New Strategy"
    this.properties.pacing_amount = options.pacing_amount || 0
    this.properties.type = options.type || "CPM"
    this.properties.version = 0
  //optional
    this.properties.status=options.status || "active"
    this.properties.audience_segment_exclude_op=options.audience_segment_exclude_op || ""
    this.properties.audience_segment_include_op=options.audience_segment_include_op || ""
    this.properties.bid_aggressiveness=options.bid_aggressiveness || ""
    this.properties.bid_price_is_media_only=options.bid_price_is_media_only || ""
    this.properties.currency_code=options.currency_code || ""
    this.properties.description=options.description || ""
    this.properties.effective_goal_value=options.effective_goal_value || ""
    this.properties.end_date=options.end_date || ""
    this.properties.frequency_amount=options.frequency_amount || ""
    this.properties.frequency_interval=options.frequency_interval || ""
    this.properties.impression_cap=options.impression_cap || ""
    this.properties.media_type=options.media_type || ""
    this.properties.pacing_interval=options.pacing_interval || ""
    this.properties.pacing_type=options.pacing_type || ""
    this.properties.pixel_target_expr=options.pixel_target_expr || ""
    this.properties.roi_target=options.roi_target || ""
    this.properties.run_on_all_exchanges=options.run_on_all_exchanges || ""
    this.properties.run_on_all_pmp=options.run_on_all_pmp || ""
    this.properties.run_on_display=options.run_on_display || ""
    this.properties.run_on_mobile=options.run_on_mobile || ""
    this.properties.run_on_streaming=options.run_on_streaming || ""
    this.properties.site_selectiveness=options.site_selectiveness || ""
    this.properties.site_restriction_transparent_urls=options.site_restriction_transparent_urls || ""
    this.properties.start_date=options.start_date || ""
    this.properties.supply_type=options.supply_type || ""
    this.properties.use_campaign_end=options.use_campaign_end || ""
    this.properties.use_campaign_start=options.use_campaign_start || ""
    this.properties.use_mm_freq=options.use_mm_freq || ""
    this.properties.use_optimization=options.use_optimization || ""
    this.properties.zone_name=options.zone_name || ""
}

var save_to_bulk_api = function(new_strategy, callback){
    var form_data = JSON.stringify(new_strategy)
    $.ajax({
        type : "POST",
        contentType : 'application/json',
        url : '/strategies/create',
        data : form_data,
        processData: false
}).done(function(resp){
    callback()
})
}


