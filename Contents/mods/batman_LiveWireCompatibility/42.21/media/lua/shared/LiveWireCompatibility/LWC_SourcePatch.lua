-- LiveWire Compatibility: source patches (ADR-006). Some target mods decide "is there power" in a
-- local function no wrapper can reach. A file of ours with the same path replaces the target's
-- file (loaded after it) and calls SourcePatch.run(path): the target's own file is read from its
-- folder (getModFileReader, LuaManager.java:4925: version folder, then common; UTF-8), each
-- declared edit is applied, and the result runs (loadstring). None of the target's code is shipped.
--   SourcePatch.add({ mod = "<mod id>", path = "media/lua/...", edits = { { old = "...", new = "..." } } })
-- Each `old` must occur exactly once; otherwise, or when the edited text does not compile, the
-- original file runs unchanged and the console says why. Without the target mod, nothing runs.
LiveWireCompat = LiveWireCompat or {}
local SP = LiveWireCompat.SourcePatch or {}
LiveWireCompat.SourcePatch = SP
SP.patches = SP.patches or {}
SP.applied = SP.applied or {}  -- path -> true, or the reason the original ran / nothing ran

local function log(msg)
    print("[LiveWireCompat] " .. msg)
end

function SP.add(patch)
    if type(patch) ~= "table" or type(patch.mod) ~= "string" or type(patch.path) ~= "string"
        or type(patch.edits) ~= "table" or #patch.edits == 0 then
        return false
    end
    for i = 1, #patch.edits do
        local e = patch.edits[i]
        if type(e) ~= "table" or type(e.old) ~= "string" or e.old == "" or type(e.new) ~= "string" then
            return false
        end
    end
    SP.patches[patch.path] = patch
    return true
end

local function active(modId)
    local mods = getActivatedMods and getActivatedMods()
    return mods ~= nil and mods:contains(modId)
end

local function read(modId, path)
    local reader = getModFileReader and getModFileReader(modId, path, false)
    if not reader then return nil end
    local lines = {}
    local line = reader:readLine()
    while line ~= nil do
        lines[#lines + 1] = line
        line = reader:readLine()
    end
    reader:close()
    return table.concat(lines, "\n") .. "\n"
end

-- Plain-text occurrences of `s` in `text`.
local function occurrences(text, s)
    local n, from = 0, 1
    while true do
        local i = string.find(text, s, from, true)
        if not i then return n end
        n = n + 1
        from = i + #s
    end
end

-- The edited text, or nil and the reason.
function SP.edit(text, edits)
    for i = 1, #edits do
        local e = edits[i]
        if occurrences(text, e.old) ~= 1 then return nil, "edit_not_found" end
        local at = string.find(text, e.old, 1, true)
        text = string.sub(text, 1, at - 1) .. e.new .. string.sub(text, at + #e.old)
    end
    return text
end

function SP.run(path)
    local patch = SP.patches[path]
    if not patch then
        log("no source patch declared for " .. tostring(path))
        return nil
    end
    if not active(patch.mod) then return nil end
    local source = read(patch.mod, path)
    if not source then
        SP.applied[path] = "unreadable"
        log("cannot read " .. patch.mod .. " " .. path .. ": nothing run")
        return nil
    end
    local name = patch.mod .. ":" .. path
    local chunk
    local edited, reason = SP.edit(source, patch.edits)
    if edited then
        chunk = loadstring(edited, name)
        if not chunk then reason = "compile_error" end
    end
    if chunk then
        SP.applied[path] = true
        log("source patch applied: " .. name)
    else
        SP.applied[path] = reason
        log("source patch not applied (" .. reason .. "), original file runs: " .. name)
        chunk = loadstring(source, name)
    end
    return chunk()
end

-- At world start: an active target whose patch never ran, because this mod loads before it.
function SP.report()
    for path, patch in pairs(SP.patches) do
        if SP.applied[path] == nil and active(patch.mod) then
            log("source patch not run for " .. patch.mod .. " " .. path
                .. ": load batman_LiveWireCompatibility after " .. patch.mod)
        end
    end
end
