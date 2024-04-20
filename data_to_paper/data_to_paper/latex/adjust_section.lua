function Header(elem)
    if elem.level == 1 then
        elem.level = 2
    elseif elem.level == 2 then
        elem.level = 3
    end
    -- You can add more adjustments if needed
    return elem
end
