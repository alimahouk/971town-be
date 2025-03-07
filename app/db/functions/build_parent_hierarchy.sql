-- Drop the existing build_parent_hierarchy function
DROP FUNCTION IF EXISTS build_parent_hierarchy(BIGINT);

-- Recursive function to build the parent hierarchy
CREATE OR REPLACE FUNCTION build_parent_hierarchy(p_parent_product_id BIGINT)
RETURNS JSONB AS $$
DECLARE
    parent_data JSONB;
BEGIN
    IF p_parent_product_id IS NULL THEN
        RETURN NULL;
    END IF;

    SELECT
        ROW_TO_JSON(p)::jsonb - 'parent_product_id' || jsonb_build_object('parent_product', build_parent_hierarchy(p.parent_product_id))
    INTO parent_data
    FROM
        product_ p
    WHERE
        p.id = p_parent_product_id;

    RETURN parent_data;
END;
$$ LANGUAGE plpgsql;

-- Main function to get the parent product hierarchy
CREATE OR REPLACE FUNCTION get_parent_product_hierarchy(p_id BIGINT)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT
        jsonb_strip_nulls(
            ROW_TO_JSON(p)::jsonb - 'parent_product_id' || jsonb_build_object('parent_product', build_parent_hierarchy(p.parent_product_id))
        )
    INTO result
    FROM
        product_ p
    WHERE
        p.id = p_id;

    RETURN result;
END;
$$ LANGUAGE plpgsql;
