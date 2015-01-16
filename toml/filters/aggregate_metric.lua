require "circular_buffer"
require "string"

local aggregation = read_config('aggregation') or error('you must initialize "aggregation" option')
local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local data = { }

for agg in string.gmatch(aggregation, "[%S]+") do
    if not agg == ("avg" or "max" or "min" or "sum" or "last") then
	error('"' .. agg .. '" unknow aggregation method: allowed values for aggregation are "avg", "sum", "max", "min", "last"')
    end
end

function min(val1, val2)
    if val1 > val2 then return val2 end
    return val1
end

function max(val1, val2)
    if val1 < val2 then return val2 end
    return val1
end

function process_message()
    local name = read_message('Fields[name]')
    local value = tonumber(read_message('Fields[value]'))

    if data[name] == nil then
	data[name] = {
	    last = value,
	    min = value,
	    max = value,
	    sum = value,
	    count = 1
	}
	return 0
    end
    
    data[name].last = value
    data[name].min = min(value, data[name].min)
    data[name].max = max(value, data[name].max)
    data[name].sum = data[name].sum + value
    data[name].count = data[name].count + 1
    return 0
end

function timer_event(ns)
    for agg in string.gmatch(aggregation, "[%S]+") do
	for name, cb in pairs(data) do
	    local value = 0
	    if agg == "avg" then
		value = data[name].sum/data[name].count
	    else
		value = data[name][agg]
	    end
	    inject_message({
		Type = type_output,
		Timestamp = ns,
		Fields = {
		    aggregation = agg,
		    value = value,
		    name = name
		}
	    })
	end
    end
    data = { }
end
