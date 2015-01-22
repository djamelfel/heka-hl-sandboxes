local type_output = read_config('type_output') or error('you must initialize "type_output" option')

function process_message()
    local fields = {
	type = "event",
	version = 0,
	log = '[' .. read_message('Fields[text]') .. ']'
    }

    while true do
	typ, name, value = read_next_field()
	if not typ then break end
	if typ ~= 1 then --exculde bytes
	    fields[name] = value
	end
    end

    inject_message({
	Type = type_output,
	Payload = read_message('Payload'),
	Timestamp = read_message('Timestamp'),
	Fields = fields
    })
    return 0
end
