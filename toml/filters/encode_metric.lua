local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local metric_version = 0

function process_message()
    local fields = {
	encoder_type = "metric",
	encoder_version = metric_version
    }

    while true do
	typ, name, value = read_next_field()
	if not typ then break end
	if typ ~= 1 then --exclude bytes
	    fields[name] = value
	end
    end

    inject_message({
	Type = type_output,
	Payload = read_message('Fields[name]') .. ' ' .. read_message('Fields[value]'),
	Timestamp = read_message('Timestamp'),
	Fields = fields
    })
    return 0
end
