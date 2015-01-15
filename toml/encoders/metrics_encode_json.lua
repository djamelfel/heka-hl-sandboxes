require "cjson"

function process_message()
    local data = {
        timestamp = read_message('Timestamp')/1e6
    }

    while true do
        typ, name, value = read_next_field()
        if not typ then break end
        if typ ~= 1 then --exclude bytes
            data[name] = value
        end
    end
    inject_payload("json", "server_db", cjson.encode(data))

    return 0
end
