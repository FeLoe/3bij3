/* http://keith-wood.name/linkedSliders.html
   Linked Sliders 1.1.0 for jQuery UI Slider 1.9.0.
   Written by Keith Wood (kbwood{at}iinet.com.au) January 2011.
   Available under the MIT (https://github.com/jquery/jquery/blob/master/MIT-LICENSE.txt) license. 
   Please attribute the authors if you use it. */

(function($) { // Hide the namespace

/* Linked Sliders manager. */
function LinkedSliders() {
	this._defaults = {
		total: 100,  // The total for all the linked sliders
		policy: 'next' // Adjustment policy: 'next', 'prev', 'first', 'last', 'all'
	};
}

$.extend(LinkedSliders.prototype, {
	/* Class name added to elements to indicate already configured with linked sliders. */
	markerClassName: 'hasLinkedSliders',
	/* Name of the data property for instance settings. */
	propertyName: 'linkedSliders',

	/* Override the default settings for all linked sliders instances.
	   @param  options  (object) the new settings to use as defaults
	   @return  (SimpleBar) this manager */
	setDefaults: function(options) {
		$.extend(this._defaults, options || {});
		return this;
	},

	/* Attach the linked sliders functionality to an element.
	   @param  target   (element) the slider to be linked
	   @param  options  (object) the new settings for this slider
	   @param  linked   (jQuery) the set of linked sliders */
	_attachPlugin: function(target, options, linked) {
		target = $(target);
		if (!target.hasClass('ui-slider')) {
			throw 'Please add slider functionality first';
		}
		if (target.hasClass(this.markerClassName)) {
			return;
		}
		var inst = {options: $.extend({}, this._defaults), linked: linked || {}};
		target.addClass(this.markerClassName).data(this.propertyName, inst);
		this._optionPlugin(target, options);
	},

	/* Retrieve or reconfigure the settings for a control.
	   @param  target   (element) the control to affect
	   @param  options  (object) the new options for this instance or
	                    (string) an individual property name
	   @param  value    (any) the individual property value (omit if options
	                    is an object or to retrieve the value of a setting)
	   @return  (any) if retrieving a value */
	_optionPlugin: function(target, options, value) {
		target = $(target);
		var inst = target.data(this.propertyName);
		if (!options || (typeof options == 'string' && value == null)) { // Get option
			var name = options;
			options = (inst || {}).options;
			return (options && name ? options[name] : options);
		}

		if (!target.hasClass(this.markerClassName)) {
			return;
		}
		options = options || {};
		if (typeof options == 'string') {
			var name = options;
			options = {};
			options[name] = value;
		}
		$.extend(inst.options, options);
		target.unbind('.' + this.propertyName).
			bind('slidechange.' + this.propertyName + ',slide.' + this.propertyName, function(event, ui) {
				if (!plugin._linking) {
					plugin._linking = true; // Prevent recursion
					plugin._linkSliders(target, event, ui);
					plugin._linking = false;
				}
			});
		plugin._linkSliders(target, null, {handle: target}); // Initial synch
	},

	/* Remove the plugin functionality from a control.
	   @param  target  (element) the control to affect */
	_destroyPlugin: function(target) {
		target = $(target);
		if (!target.hasClass(this.markerClassName)) {
			return;
		}
		target.removeClass(this.markerClassName).removeData(this.propertyName).
			unbind('.' + this.propertyName);
	},

	/* Update the set of linked sliders.
	   @param  target  (element) the slider element being changed
	   @param  event   (Event) the change event
	   @param  ui      (object) the current UI settings */
	_linkSliders: function(target, event, ui) {
		var inst = target.data(this.propertyName);
		var linked = inst.linked.length ? inst.linked : $([]);
		var curIndex = linked.index($(ui.handle).closest('.ui-slider'));
		var remTotal = inst.options.total;
		linked.each(function(i) {
			remTotal -= $(this).slider('value');
		});
		var dir = ($.inArray(inst.options.policy, ['prev', 'last']) > -1 ? -1 : +1);
		var index = (inst.options.policy == 'first' ? 0 :
			(inst.options.policy == 'last' ? linked.length - 1 : curIndex));
		for (var i = 0; i < 2 * linked.length; i++) {
			if (index != curIndex) {
				var slider = linked.eq(index);
				var val = slider.slider('value');
				var min = slider.slider('option', 'min');
				var max = slider.slider('option', 'max');
				var newVal = 0;
				if (inst.options.policy == 'all') {
					newVal = (i == linked.length - 1 ? remTotal :
						Math.floor(remTotal / Math.max(1, linked.length - i)));
					newVal = Math.min(Math.max(val + newVal, min), max);
				}
				else {
					newVal = Math.min(Math.max(val + remTotal, min), max);
				}
				slider.slider('value', newVal);
				remTotal -= (newVal - val);
				if (remTotal == 0) {
					break;
				}
			}
			index = (linked.length + index + dir) % linked.length;
		}
	}
});

// The list of commands that return values and don't permit chaining
var getters = [''];

/* Determine whether a command is a getter and doesn't permit chaining.
   @param  command    (string, optional) the command to run
   @param  otherArgs  ([], optional) any other arguments for the command
   @return  true if the command is a getter, false if not */
function isNotChained(command, otherArgs) {
	if (command == 'option' && (otherArgs.length == 0 ||
			(otherArgs.length == 1 && typeof otherArgs[0] == 'string'))) {
		return true;
	}
	return $.inArray(command, getters) > -1;
}

/* Attach the linked sliders functionality to a jQuery selection.
   @param  options  (object) the new settings to use for these instances (optional) or
                    (string) the command to run (optional)
   @return  (jQuery) for chaining further calls or
            (any) getter value */
$.fn.linkedSliders = function(options) {
	var otherArgs = Array.prototype.slice.call(arguments, 1);
	if (isNotChained(options, otherArgs)) {
		return plugin['_' + options + 'Plugin'].apply(plugin, [this[0]].concat(otherArgs));
	}
	var linked = this;
	return this.each(function() {
		if (typeof options == 'string') {
			if (!plugin['_' + options + 'Plugin']) {
				throw 'Unknown command: ' + options;
			}
			plugin['_' + options + 'Plugin'].apply(plugin, [this].concat(otherArgs));
		}
		else {
			plugin._attachPlugin(this, options || {}, linked);
		}
	});
};

/* Initialise the linked sliders functionality. */
var plugin = $.linkedSliders = new LinkedSliders(); // Singleton instance

})(jQuery);
