--
-- PostgreSQL database dump
--

-- Dumped from database version 14.6 (Homebrew)
-- Dumped by pg_dump version 15.1

-- Started on 2023-03-02 08:56:27 +04

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 4902 (class 1262 OID 16385)
-- Name: 971town; Type: DATABASE; Schema: -; Owner: postgres
--

CREATE DATABASE "971town" WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'C';


ALTER DATABASE "971town" OWNER TO postgres;

\connect "971town"

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 5 (class 2615 OID 2200)
-- Name: public; Type: SCHEMA; Schema: -; Owner: mahouk
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO mahouk;

--
-- TOC entry 2 (class 3079 OID 16424)
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- TOC entry 4904 (class 0 OID 0)
-- Dependencies: 2
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry and geography spatial types and functions';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 221 (class 1259 OID 17525)
-- Name: admin_user_account_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.admin_user_account_ (
    user_account_id bigint NOT NULL,
    creation_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.admin_user_account_ OWNER TO postgres;

--
-- TOC entry 276 (class 1259 OID 19226)
-- Name: alias_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alias_ (
    alias character varying(64) NOT NULL,
    entity_type smallint NOT NULL,
    ts_alias tsvector GENERATED ALWAYS AS (to_tsvector('english'::regconfig, (alias)::text)) STORED NOT NULL,
    id bigint NOT NULL
);


ALTER TABLE public.alias_ OWNER TO postgres;

--
-- TOC entry 229 (class 1259 OID 17648)
-- Name: badge_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.badge_ (
    id integer NOT NULL,
    name character varying(64) NOT NULL,
    description character varying NOT NULL,
    creation_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.badge_ OWNER TO postgres;

--
-- TOC entry 228 (class 1259 OID 17647)
-- Name: badge_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.badge_ ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.badge_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 216 (class 1259 OID 17475)
-- Name: brand_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.brand_ (
    id bigint NOT NULL,
    name character varying(128) NOT NULL,
    creation_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    creator_id bigint,
    alias character varying(64) NOT NULL,
    rep integer DEFAULT 1 NOT NULL,
    website character varying,
    description character varying,
    edit_access_level smallint DEFAULT 1 NOT NULL,
    visibility smallint DEFAULT 1 NOT NULL,
    ts_name tsvector GENERATED ALWAYS AS (((setweight(to_tsvector('english'::regconfig, (COALESCE(name, ''::character varying))::text), 'A'::"char") || setweight(to_tsvector('english'::regconfig, (COALESCE(alias, ''::character varying))::text), 'B'::"char")) || setweight(to_tsvector('english'::regconfig, (COALESCE(description, ''::character varying))::text), 'C'::"char"))) STORED,
    avatar_light_path character varying
);


ALTER TABLE public.brand_ OWNER TO postgres;

--
-- TOC entry 4905 (class 0 OID 0)
-- Dependencies: 216
-- Name: COLUMN brand_.website; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.brand_.website IS 'The brand''s main website.';


--
-- TOC entry 4906 (class 0 OID 0)
-- Dependencies: 216
-- Name: COLUMN brand_.visibility; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.brand_.visibility IS 'Visible, hidden, removed, or deleted.';


--
-- TOC entry 251 (class 1259 OID 18249)
-- Name: brand_edit_history_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.brand_edit_history_ (
    edit_id bigint NOT NULL,
    edit_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    editor_id bigint,
    brand_id bigint NOT NULL,
    field_value character varying,
    field_id smallint,
    action_id smallint NOT NULL
);


ALTER TABLE public.brand_edit_history_ OWNER TO postgres;

--
-- TOC entry 215 (class 1259 OID 17474)
-- Name: brand_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.brand_ ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.brand_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 241 (class 1259 OID 17834)
-- Name: brand_manager_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.brand_manager_ (
    user_account_id bigint NOT NULL,
    brand_id bigint NOT NULL,
    creation_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.brand_manager_ OWNER TO postgres;

--
-- TOC entry 250 (class 1259 OID 18248)
-- Name: brand_name_history__edit_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.brand_edit_history_ ALTER COLUMN edit_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.brand_name_history__edit_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 237 (class 1259 OID 17765)
-- Name: brand_report_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.brand_report_ (
    id bigint NOT NULL,
    brand_id bigint NOT NULL,
    type smallint NOT NULL,
    creation_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    reporter_id bigint,
    comment character varying
);


ALTER TABLE public.brand_report_ OWNER TO postgres;

--
-- TOC entry 236 (class 1259 OID 17764)
-- Name: brand_report_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.brand_report_ ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.brand_report_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 271 (class 1259 OID 18832)
-- Name: brand_tag_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.brand_tag_ (
    brand_id bigint NOT NULL,
    tag_id bigint NOT NULL
);


ALTER TABLE public.brand_tag_ OWNER TO postgres;

--
-- TOC entry 269 (class 1259 OID 18602)
-- Name: brand_view_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.brand_view_ (
    brand_id bigint NOT NULL,
    user_account_id bigint,
    ip_address inet,
    frequency integer DEFAULT 1 NOT NULL
);


ALTER TABLE public.brand_view_ OWNER TO postgres;

--
-- TOC entry 260 (class 1259 OID 18390)
-- Name: continent_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.continent_ (
    code character(2) NOT NULL,
    name character varying(256) NOT NULL
);


ALTER TABLE public.continent_ OWNER TO postgres;

--
-- TOC entry 261 (class 1259 OID 18395)
-- Name: country_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.country_ (
    alpha_2_code character(2) NOT NULL,
    name character varying(256) NOT NULL,
    full_name character varying(256) NOT NULL,
    alpha_3_code character(3) NOT NULL,
    numeric_3_code character(3) NOT NULL,
    continent_code character(2) NOT NULL,
    is_enabled boolean DEFAULT false NOT NULL,
    currency_code character(3)
);


ALTER TABLE public.country_ OWNER TO postgres;

--
-- TOC entry 4907 (class 0 OID 0)
-- Dependencies: 261
-- Name: COLUMN country_.alpha_2_code; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.country_.alpha_2_code IS 'Two-letter country code (ISO 3166-1 alpha-2).';


--
-- TOC entry 4908 (class 0 OID 0)
-- Dependencies: 261
-- Name: COLUMN country_.name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.country_.name IS 'English country name.';


--
-- TOC entry 4909 (class 0 OID 0)
-- Dependencies: 261
-- Name: COLUMN country_.full_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.country_.full_name IS 'Full English country name.';


--
-- TOC entry 4910 (class 0 OID 0)
-- Dependencies: 261
-- Name: COLUMN country_.alpha_3_code; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.country_.alpha_3_code IS 'Three-letter country code (ISO 3166-1 alpha-3).';


--
-- TOC entry 4911 (class 0 OID 0)
-- Dependencies: 261
-- Name: COLUMN country_.numeric_3_code; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.country_.numeric_3_code IS 'Three-digit country number (ISO 3166-1 numeric).';


--
-- TOC entry 265 (class 1259 OID 18474)
-- Name: country_dialing_code_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.country_dialing_code_ (
    id smallint NOT NULL,
    alpha_2_code character(2) NOT NULL,
    code character varying NOT NULL
);


ALTER TABLE public.country_dialing_code_ OWNER TO postgres;

--
-- TOC entry 264 (class 1259 OID 18473)
-- Name: country_dialing_code__id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.country_dialing_code_ ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.country_dialing_code__id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 270 (class 1259 OID 18814)
-- Name: currency_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.currency_ (
    code character(3) NOT NULL,
    symbol character varying
);


ALTER TABLE public.currency_ OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 17507)
-- Name: locality_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.locality_ (
    id bigint NOT NULL,
    name character varying(128) NOT NULL,
    alpha_2_code character(2) NOT NULL,
    creation_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ts_name tsvector GENERATED ALWAYS AS (to_tsvector('english'::regconfig, (name)::text)) STORED,
    name_clean character varying NOT NULL
);


ALTER TABLE public.locality_ OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 17506)
-- Name: locality_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.locality_ ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.locality_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 224 (class 1259 OID 17553)
-- Name: product_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.product_ (
    id bigint NOT NULL,
    brand_id bigint,
    name character varying(128),
    creation_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    creator_id bigint,
    alias character varying(64),
    description character varying,
    url character varying,
    edit_access_level smallint DEFAULT 1 NOT NULL,
    visibility smallint DEFAULT 1 NOT NULL,
    ts_name tsvector GENERATED ALWAYS AS (((setweight(to_tsvector('english'::regconfig, (COALESCE(name, ''::character varying))::text), 'A'::"char") || setweight(to_tsvector('english'::regconfig, (COALESCE(alias, ''::character varying))::text), 'B'::"char")) || setweight(to_tsvector('english'::regconfig, (COALESCE(description, ''::character varying))::text), 'C'::"char"))) STORED,
    upc character varying,
    main_color character varying,
    material character varying,
    parent_product_id bigint
);


ALTER TABLE public.product_ OWNER TO postgres;

--
-- TOC entry 4912 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN product_.description; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.product_.description IS 'The brand''s description of the product.';


--
-- TOC entry 4913 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN product_.url; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.product_.url IS 'The URL to the product on the brand''s website.';


--
-- TOC entry 4914 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN product_.visibility; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.product_.visibility IS 'Visible, hidden, removed, or deleted.';


--
-- TOC entry 253 (class 1259 OID 18298)
-- Name: product_edit_history_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.product_edit_history_ (
    edit_id bigint NOT NULL,
    edit_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    editor_id bigint,
    product_id bigint NOT NULL,
    field_value character varying,
    field_id smallint,
    action_id smallint NOT NULL
);


ALTER TABLE public.product_edit_history_ OWNER TO postgres;

--
-- TOC entry 252 (class 1259 OID 18297)
-- Name: product_edit_history__edit_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.product_edit_history_ ALTER COLUMN edit_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.product_edit_history__edit_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 223 (class 1259 OID 17552)
-- Name: product_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.product_ ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.product_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 240 (class 1259 OID 17818)
-- Name: product_manager_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.product_manager_ (
    user_account_id bigint NOT NULL,
    product_id bigint NOT NULL,
    creation_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.product_manager_ OWNER TO postgres;

--
-- TOC entry 232 (class 1259 OID 17726)
-- Name: product_report_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.product_report_ (
    id bigint NOT NULL,
    product_id bigint NOT NULL,
    type smallint NOT NULL,
    creation_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    reporter_id bigint NOT NULL,
    comment character varying
);


ALTER TABLE public.product_report_ OWNER TO postgres;

--
-- TOC entry 233 (class 1259 OID 17744)
-- Name: product_report_report_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.product_report_ ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.product_report_report_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 227 (class 1259 OID 17610)
-- Name: product_tag_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.product_tag_ (
    product_id bigint NOT NULL,
    tag_id bigint NOT NULL
);


ALTER TABLE public.product_tag_ OWNER TO postgres;

--
-- TOC entry 273 (class 1259 OID 18863)
-- Name: product_view_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.product_view_ (
    product_id bigint NOT NULL,
    user_account_id bigint,
    ip_address inet,
    frequency integer DEFAULT 1 NOT NULL
);


ALTER TABLE public.product_view_ OWNER TO postgres;

--
-- TOC entry 231 (class 1259 OID 17693)
-- Name: product_vote_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.product_vote_ (
    product_id bigint NOT NULL,
    user_id bigint NOT NULL,
    vote boolean DEFAULT true NOT NULL,
    creation_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.product_vote_ OWNER TO postgres;

--
-- TOC entry 218 (class 1259 OID 17487)
-- Name: store_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.store_ (
    id bigint NOT NULL,
    alias character varying(64) NOT NULL,
    name character varying(128),
    brand_id bigint,
    creation_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    creator_id bigint,
    description character varying,
    locality_id bigint NOT NULL,
    post_code character varying,
    street character varying,
    building character varying,
    floor character varying,
    unit character varying,
    website character varying,
    edit_access_level smallint DEFAULT 1 NOT NULL,
    post_access_level smallint DEFAULT 1 NOT NULL,
    visibility smallint DEFAULT 1 NOT NULL,
    ts_name tsvector GENERATED ALWAYS AS (((setweight(to_tsvector('english'::regconfig, (COALESCE(name, ''::character varying))::text), 'A'::"char") || setweight(to_tsvector('english'::regconfig, (COALESCE(alias, ''::character varying))::text), 'B'::"char")) || setweight(to_tsvector('english'::regconfig, (COALESCE(description, ''::character varying))::text), 'C'::"char"))) STORED,
    coordinates public.geography,
    status smallint DEFAULT 1 NOT NULL
);


ALTER TABLE public.store_ OWNER TO postgres;

--
-- TOC entry 4915 (class 0 OID 0)
-- Dependencies: 218
-- Name: COLUMN store_.website; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.store_.website IS 'For cases where a specific store has its own website indepent of the store brand''s main website.';


--
-- TOC entry 4916 (class 0 OID 0)
-- Dependencies: 218
-- Name: COLUMN store_.visibility; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.store_.visibility IS 'Visible, hidden, removed, or deleted.';


--
-- TOC entry 4917 (class 0 OID 0)
-- Dependencies: 218
-- Name: COLUMN store_.status; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.store_.status IS 'The store''s current operational status.';


--
-- TOC entry 255 (class 1259 OID 18329)
-- Name: store_edit_history_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.store_edit_history_ (
    edit_id bigint NOT NULL,
    edit_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    editor_id bigint,
    store_id bigint NOT NULL,
    field_value character varying,
    field_id smallint,
    action_id smallint NOT NULL
);


ALTER TABLE public.store_edit_history_ OWNER TO postgres;

--
-- TOC entry 254 (class 1259 OID 18328)
-- Name: store_edit_history__edit_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.store_edit_history_ ALTER COLUMN edit_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.store_edit_history__edit_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 217 (class 1259 OID 17486)
-- Name: store_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.store_ ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.store_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 222 (class 1259 OID 17536)
-- Name: store_manager_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.store_manager_ (
    user_account_id bigint NOT NULL,
    store_id bigint NOT NULL,
    creation_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.store_manager_ OWNER TO postgres;

--
-- TOC entry 259 (class 1259 OID 18364)
-- Name: store_product_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.store_product_ (
    id bigint NOT NULL,
    store_id bigint NOT NULL,
    product_id bigint NOT NULL,
    creation_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    creator_id bigint,
    price numeric(14,2) NOT NULL,
    release_timestamp timestamp with time zone,
    description character varying,
    url character varying,
    condition character varying
);


ALTER TABLE public.store_product_ OWNER TO postgres;

--
-- TOC entry 258 (class 1259 OID 18363)
-- Name: store_product__listing_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.store_product_ ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.store_product__listing_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 257 (class 1259 OID 18349)
-- Name: store_product_history_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.store_product_history_ (
    edit_id bigint NOT NULL,
    edit_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    editor_id bigint,
    store_product_id bigint NOT NULL,
    field_value character varying,
    field_id smallint,
    action_id smallint NOT NULL
);


ALTER TABLE public.store_product_history_ OWNER TO postgres;

--
-- TOC entry 256 (class 1259 OID 18348)
-- Name: store_product_history__edit_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.store_product_history_ ALTER COLUMN edit_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.store_product_history__edit_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 235 (class 1259 OID 17746)
-- Name: store_report_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.store_report_ (
    id bigint NOT NULL,
    store_id bigint NOT NULL,
    type smallint NOT NULL,
    creation_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    reporter_id bigint NOT NULL,
    comment character varying
);


ALTER TABLE public.store_report_ OWNER TO postgres;

--
-- TOC entry 234 (class 1259 OID 17745)
-- Name: store_report_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.store_report_ ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.store_report_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 249 (class 1259 OID 18227)
-- Name: store_shadow_ban_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.store_shadow_ban_ (
    store_id bigint NOT NULL,
    creation_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    imposer_id bigint
);


ALTER TABLE public.store_shadow_ban_ OWNER TO postgres;

--
-- TOC entry 243 (class 1259 OID 17927)
-- Name: store_tag_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.store_tag_ (
    store_id bigint NOT NULL,
    tag_id bigint NOT NULL
);


ALTER TABLE public.store_tag_ OWNER TO postgres;

--
-- TOC entry 272 (class 1259 OID 18847)
-- Name: store_view_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.store_view_ (
    store_id bigint NOT NULL,
    user_account_id bigint,
    ip_address inet,
    frequency integer DEFAULT 1 NOT NULL
);


ALTER TABLE public.store_view_ OWNER TO postgres;

--
-- TOC entry 226 (class 1259 OID 17602)
-- Name: tag_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tag_ (
    id bigint NOT NULL,
    name character varying(64) NOT NULL,
    creation_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    creator_id bigint,
    ts_name tsvector GENERATED ALWAYS AS (to_tsvector('english'::regconfig, (name)::text)) STORED
);


ALTER TABLE public.tag_ OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 17601)
-- Name: tag_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.tag_ ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.tag_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 245 (class 1259 OID 17944)
-- Name: user_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_ (
    id bigint NOT NULL,
    creation_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.user_ OWNER TO postgres;

--
-- TOC entry 247 (class 1259 OID 17962)
-- Name: user_account_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_account_ (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    alias character varying(64) NOT NULL,
    creation_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    rep integer DEFAULT 1 NOT NULL,
    bio character varying,
    website character varying,
    ts_alias tsvector GENERATED ALWAYS AS (to_tsvector('english'::regconfig, (alias)::text)) STORED
);


ALTER TABLE public.user_account_ OWNER TO postgres;

--
-- TOC entry 246 (class 1259 OID 17961)
-- Name: user_account__id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.user_account_ ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.user_account__id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 230 (class 1259 OID 17657)
-- Name: user_account_badge_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_account_badge_ (
    badge_id integer NOT NULL,
    user_account_id bigint NOT NULL,
    creation_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.user_account_badge_ OWNER TO postgres;

--
-- TOC entry 239 (class 1259 OID 17779)
-- Name: user_account_report_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_account_report_ (
    id bigint NOT NULL,
    user_account_id bigint NOT NULL,
    type smallint NOT NULL,
    creation_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    reporter_account_id bigint,
    comment character varying
);


ALTER TABLE public.user_account_report_ OWNER TO postgres;

--
-- TOC entry 242 (class 1259 OID 17913)
-- Name: user_account_session_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_account_session_ (
    id character varying(64) NOT NULL,
    user_account_id bigint NOT NULL,
    creation_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_activity timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ip_address inet,
    mac_address macaddr,
    device_type smallint,
    device_name character varying,
    client_version character varying,
    mobile_carrier character varying,
    location character varying,
    time_zone character varying,
    screen_resolution character varying,
    os_id smallint,
    os_version character varying,
    client_id character varying
);


ALTER TABLE public.user_account_session_ OWNER TO postgres;

--
-- TOC entry 4918 (class 0 OID 0)
-- Dependencies: 242
-- Name: COLUMN user_account_session_.device_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.user_account_session_.device_name IS 'The name of the device when available, e.g. Foo''s iPhone.';


--
-- TOC entry 274 (class 1259 OID 18879)
-- Name: user_account_view_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_account_view_ (
    user_account_id bigint NOT NULL,
    viewer_account_id bigint,
    ip_address inet,
    frequency integer DEFAULT 1 NOT NULL
);


ALTER TABLE public.user_account_view_ OWNER TO postgres;

--
-- TOC entry 275 (class 1259 OID 19211)
-- Name: user_client_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_client_ (
    id character varying NOT NULL,
    name character varying(128) NOT NULL,
    creation_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.user_client_ OWNER TO postgres;

--
-- TOC entry 244 (class 1259 OID 17942)
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.user_ ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 262 (class 1259 OID 18444)
-- Name: user_os_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_os_ (
    id smallint NOT NULL,
    name character varying NOT NULL
);


ALTER TABLE public.user_os_ OWNER TO postgres;

--
-- TOC entry 263 (class 1259 OID 18463)
-- Name: user_os__id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.user_os_ ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.user_os__id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 266 (class 1259 OID 18528)
-- Name: user_phone_number_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_phone_number_ (
    id bigint NOT NULL,
    dialing_code_id smallint NOT NULL,
    phone_number character varying NOT NULL,
    user_id bigint,
    creation_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_verified boolean DEFAULT false NOT NULL
);


ALTER TABLE public.user_phone_number_ OWNER TO postgres;

--
-- TOC entry 4919 (class 0 OID 0)
-- Dependencies: 266
-- Name: COLUMN user_phone_number_.user_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.user_phone_number_.user_id IS 'Allow this column to be nullable because phone numbers are staged in this table while a potential new user is verifying their number to join.';


--
-- TOC entry 268 (class 1259 OID 18565)
-- Name: user_phone_number__id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.user_phone_number_ ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.user_phone_number__id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 267 (class 1259 OID 18548)
-- Name: user_phone_number_verification_code_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_phone_number_verification_code_ (
    phone_number_id bigint NOT NULL,
    verification_code character varying NOT NULL,
    creation_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    attempts smallint DEFAULT 0 NOT NULL
);


ALTER TABLE public.user_phone_number_verification_code_ OWNER TO postgres;

--
-- TOC entry 4920 (class 0 OID 0)
-- Dependencies: 267
-- Name: COLUMN user_phone_number_verification_code_.attempts; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.user_phone_number_verification_code_.attempts IS 'Attempts made at entering the verification code. Use for added security to delete the code after a number of failed attempts.';


--
-- TOC entry 238 (class 1259 OID 17778)
-- Name: user_report_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.user_account_report_ ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.user_report_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 248 (class 1259 OID 18210)
-- Name: user_shadow_ban_; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_shadow_ban_ (
    user_id bigint NOT NULL,
    store_id bigint,
    creation_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    imposer_id bigint
);


ALTER TABLE public.user_shadow_ban_ OWNER TO postgres;

--
-- TOC entry 4593 (class 2606 OID 17530)
-- Name: admin_user_account_ admin_user_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admin_user_account_
    ADD CONSTRAINT admin_user_pkey PRIMARY KEY (user_account_id);


--
-- TOC entry 4682 (class 2606 OID 19249)
-- Name: alias_ alias_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alias_
    ADD CONSTRAINT alias_pkey PRIMARY KEY (alias);


--
-- TOC entry 4685 (class 2606 OID 19247)
-- Name: alias_ alias_uq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alias_
    ADD CONSTRAINT alias_uq UNIQUE (alias);


--
-- TOC entry 4609 (class 2606 OID 17655)
-- Name: badge_ badge_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.badge_
    ADD CONSTRAINT badge_pkey PRIMARY KEY (id);


--
-- TOC entry 4578 (class 2606 OID 18576)
-- Name: brand_ brand_alias_uq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.brand_
    ADD CONSTRAINT brand_alias_uq UNIQUE (alias);


--
-- TOC entry 4646 (class 2606 OID 18255)
-- Name: brand_edit_history_ brand_edit_history_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.brand_edit_history_
    ADD CONSTRAINT brand_edit_history_pkey PRIMARY KEY (edit_id);


--
-- TOC entry 4625 (class 2606 OID 17839)
-- Name: brand_manager_ brand_manager_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.brand_manager_
    ADD CONSTRAINT brand_manager_pkey PRIMARY KEY (user_account_id, brand_id);


--
-- TOC entry 4580 (class 2606 OID 17480)
-- Name: brand_ brand_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.brand_
    ADD CONSTRAINT brand_pkey PRIMARY KEY (id);


--
-- TOC entry 4619 (class 2606 OID 17772)
-- Name: brand_report_ brand_report_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.brand_report_
    ADD CONSTRAINT brand_report_pkey PRIMARY KEY (id);


--
-- TOC entry 4677 (class 2606 OID 18836)
-- Name: brand_tag_ brand_tag_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.brand_tag_
    ADD CONSTRAINT brand_tag_pkey PRIMARY KEY (brand_id, tag_id);


--
-- TOC entry 4661 (class 2606 OID 18394)
-- Name: continent_ continent_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.continent_
    ADD CONSTRAINT continent_pkey PRIMARY KEY (code);


--
-- TOC entry 4667 (class 2606 OID 18480)
-- Name: country_dialing_code_ country_dialing_code_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.country_dialing_code_
    ADD CONSTRAINT country_dialing_code_pkey PRIMARY KEY (id);


--
-- TOC entry 4663 (class 2606 OID 18401)
-- Name: country_ country_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.country_
    ADD CONSTRAINT country_pkey PRIMARY KEY (alpha_2_code);


--
-- TOC entry 4675 (class 2606 OID 18820)
-- Name: currency_ currency_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.currency_
    ADD CONSTRAINT currency_pkey PRIMARY KEY (code);


--
-- TOC entry 4590 (class 2606 OID 17511)
-- Name: locality_ locality_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.locality_
    ADD CONSTRAINT locality_pkey PRIMARY KEY (id);


--
-- TOC entry 4597 (class 2606 OID 18578)
-- Name: product_ product_alias_uq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_
    ADD CONSTRAINT product_alias_uq UNIQUE (alias);


--
-- TOC entry 4648 (class 2606 OID 18305)
-- Name: product_edit_history_ product_edit_history_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_edit_history_
    ADD CONSTRAINT product_edit_history_pkey PRIMARY KEY (edit_id);


--
-- TOC entry 4623 (class 2606 OID 17823)
-- Name: product_manager_ product_manager_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_manager_
    ADD CONSTRAINT product_manager_pkey PRIMARY KEY (user_account_id, product_id);


--
-- TOC entry 4599 (class 2606 OID 17559)
-- Name: product_ product_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_
    ADD CONSTRAINT product_pkey PRIMARY KEY (id);


--
-- TOC entry 4615 (class 2606 OID 17733)
-- Name: product_report_ product_report_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_report_
    ADD CONSTRAINT product_report_pkey PRIMARY KEY (reporter_id);


--
-- TOC entry 4607 (class 2606 OID 17614)
-- Name: product_tag_ product_tag_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_tag_
    ADD CONSTRAINT product_tag_pkey PRIMARY KEY (product_id, tag_id);


--
-- TOC entry 4613 (class 2606 OID 17699)
-- Name: product_vote_ product_variant_vote_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_vote_
    ADD CONSTRAINT product_variant_vote_pkey PRIMARY KEY (product_id, user_id);


--
-- TOC entry 4583 (class 2606 OID 18580)
-- Name: store_ store_alias_uq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_
    ADD CONSTRAINT store_alias_uq UNIQUE (alias);


--
-- TOC entry 4651 (class 2606 OID 18336)
-- Name: store_edit_history_ store_edit_history_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_edit_history_
    ADD CONSTRAINT store_edit_history_pkey PRIMARY KEY (edit_id);


--
-- TOC entry 4595 (class 2606 OID 17541)
-- Name: store_manager_ store_manager_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_manager_
    ADD CONSTRAINT store_manager_pkey PRIMARY KEY (user_account_id, store_id);


--
-- TOC entry 4586 (class 2606 OID 17494)
-- Name: store_ store_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_
    ADD CONSTRAINT store_pkey PRIMARY KEY (id);


--
-- TOC entry 4654 (class 2606 OID 18356)
-- Name: store_product_history_ store_product_history_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_product_history_
    ADD CONSTRAINT store_product_history_pkey PRIMARY KEY (edit_id);


--
-- TOC entry 4657 (class 2606 OID 18371)
-- Name: store_product_ store_product_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_product_
    ADD CONSTRAINT store_product_pkey PRIMARY KEY (id);


--
-- TOC entry 4659 (class 2606 OID 18373)
-- Name: store_product_ store_product_uq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_product_
    ADD CONSTRAINT store_product_uq UNIQUE (store_id, product_id);


--
-- TOC entry 4617 (class 2606 OID 17753)
-- Name: store_report_ store_report_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_report_
    ADD CONSTRAINT store_report_pkey PRIMARY KEY (id);


--
-- TOC entry 4643 (class 2606 OID 18232)
-- Name: store_shadow_ban_ store_shadow_ban__pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_shadow_ban_
    ADD CONSTRAINT store_shadow_ban__pkey PRIMARY KEY (store_id);


--
-- TOC entry 4629 (class 2606 OID 17931)
-- Name: store_tag_ store_tag_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_tag_
    ADD CONSTRAINT store_tag_pkey PRIMARY KEY (tag_id, store_id);


--
-- TOC entry 4602 (class 2606 OID 17608)
-- Name: tag_ tag_name_uq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tag_
    ADD CONSTRAINT tag_name_uq UNIQUE (name);


--
-- TOC entry 4604 (class 2606 OID 17606)
-- Name: tag_ tag_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tag_
    ADD CONSTRAINT tag_pkey PRIMARY KEY (id);


--
-- TOC entry 4633 (class 2606 OID 18465)
-- Name: user_account_ user_account_alias_uq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_account_
    ADD CONSTRAINT user_account_alias_uq UNIQUE (alias);


--
-- TOC entry 4635 (class 2606 OID 17970)
-- Name: user_account_ user_account_id_uq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_account_
    ADD CONSTRAINT user_account_id_uq UNIQUE (id);


--
-- TOC entry 4637 (class 2606 OID 17966)
-- Name: user_account_ user_account_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_account_
    ADD CONSTRAINT user_account_pkey PRIMARY KEY (id, user_id);


--
-- TOC entry 4611 (class 2606 OID 17662)
-- Name: user_account_badge_ user_badge_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_account_badge_
    ADD CONSTRAINT user_badge_pkey PRIMARY KEY (badge_id, user_account_id);


--
-- TOC entry 4680 (class 2606 OID 19217)
-- Name: user_client_ user_client_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_client_
    ADD CONSTRAINT user_client_pkey PRIMARY KEY (id);


--
-- TOC entry 4665 (class 2606 OID 18450)
-- Name: user_os_ user_os_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_os_
    ADD CONSTRAINT user_os_pkey PRIMARY KEY (id);


--
-- TOC entry 4669 (class 2606 OID 18535)
-- Name: user_phone_number_ user_phone_number_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_phone_number_
    ADD CONSTRAINT user_phone_number_pkey PRIMARY KEY (id);


--
-- TOC entry 4671 (class 2606 OID 18537)
-- Name: user_phone_number_ user_phone_number_uq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_phone_number_
    ADD CONSTRAINT user_phone_number_uq UNIQUE (dialing_code_id, phone_number, user_id);


--
-- TOC entry 4673 (class 2606 OID 18552)
-- Name: user_phone_number_verification_code_ user_phone_number_verification_code_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_phone_number_verification_code_
    ADD CONSTRAINT user_phone_number_verification_code_pkey PRIMARY KEY (phone_number_id);


--
-- TOC entry 4631 (class 2606 OID 17972)
-- Name: user_ user_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- TOC entry 4621 (class 2606 OID 17783)
-- Name: user_account_report_ user_report_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_account_report_
    ADD CONSTRAINT user_report_pkey PRIMARY KEY (id);


--
-- TOC entry 4627 (class 2606 OID 17921)
-- Name: user_account_session_ user_session_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_account_session_
    ADD CONSTRAINT user_session_pkey PRIMARY KEY (id);


--
-- TOC entry 4641 (class 2606 OID 18215)
-- Name: user_shadow_ban_ user_shadow_ban_uq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_shadow_ban_
    ADD CONSTRAINT user_shadow_ban_uq UNIQUE (user_id, store_id);


--
-- TOC entry 4683 (class 1259 OID 19250)
-- Name: alias_ts_alias_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX alias_ts_alias_idx ON public.alias_ USING gin (ts_alias);


--
-- TOC entry 4644 (class 1259 OID 18266)
-- Name: brand_edit_history_brand_id_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX brand_edit_history_brand_id_idx ON public.brand_edit_history_ USING btree (brand_id);


--
-- TOC entry 4581 (class 1259 OID 18702)
-- Name: brand_ts_name_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX brand_ts_name_idx ON public.brand_ USING gin (ts_name);


--
-- TOC entry 4588 (class 1259 OID 18805)
-- Name: locality_name_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX locality_name_idx ON public.locality_ USING btree (name_clean);


--
-- TOC entry 4591 (class 1259 OID 18646)
-- Name: locality_ts_name_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX locality_ts_name_idx ON public.locality_ USING gin (ts_name);


--
-- TOC entry 4649 (class 1259 OID 18306)
-- Name: product_edit_history_product_id_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX product_edit_history_product_id_idx ON public.product_edit_history_ USING btree (product_id);


--
-- TOC entry 4600 (class 1259 OID 18693)
-- Name: product_ts_name_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX product_ts_name_idx ON public.product_ USING gin (ts_name);


--
-- TOC entry 4584 (class 1259 OID 18806)
-- Name: store_coordinates_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX store_coordinates_idx ON public.store_ USING gist (coordinates);


--
-- TOC entry 4652 (class 1259 OID 18337)
-- Name: store_edit_history_store_id_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX store_edit_history_store_id_idx ON public.store_edit_history_ USING btree (store_id);


--
-- TOC entry 4655 (class 1259 OID 18357)
-- Name: store_product_history_store_product_id_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX store_product_history_store_product_id_idx ON public.store_product_history_ USING btree (store_product_id);


--
-- TOC entry 4587 (class 1259 OID 18684)
-- Name: store_ts_name_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX store_ts_name_idx ON public.store_ USING gin (ts_name);


--
-- TOC entry 4605 (class 1259 OID 18657)
-- Name: tag_ts_name_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX tag_ts_name_idx ON public.tag_ USING gin (ts_name);


--
-- TOC entry 4638 (class 1259 OID 18721)
-- Name: user_account_ts_name_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX user_account_ts_name_idx ON public.user_account_ USING gin (ts_alias);


--
-- TOC entry 4678 (class 1259 OID 19224)
-- Name: user_client_name_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX user_client_name_idx ON public.user_client_ USING btree (name);


--
-- TOC entry 4639 (class 1259 OID 18226)
-- Name: user_shadow_ban_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX user_shadow_ban_idx ON public.user_shadow_ban_ USING btree (user_id);


--
-- TOC entry 4691 (class 2606 OID 18003)
-- Name: admin_user_account_ admin_user_user_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admin_user_account_
    ADD CONSTRAINT admin_user_user_account_id_fkey FOREIGN KEY (user_account_id) REFERENCES public.user_account_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4686 (class 2606 OID 18023)
-- Name: brand_ brand_creator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.brand_
    ADD CONSTRAINT brand_creator_id_fkey FOREIGN KEY (creator_id) REFERENCES public.user_account_(id) ON UPDATE CASCADE ON DELETE SET NULL NOT VALID;


--
-- TOC entry 4727 (class 2606 OID 18261)
-- Name: brand_edit_history_ brand_edit_history_brand_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.brand_edit_history_
    ADD CONSTRAINT brand_edit_history_brand_id_fkey FOREIGN KEY (brand_id) REFERENCES public.brand_(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- TOC entry 4728 (class 2606 OID 18256)
-- Name: brand_edit_history_ brand_edit_history_editor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.brand_edit_history_
    ADD CONSTRAINT brand_edit_history_editor_id_fkey FOREIGN KEY (editor_id) REFERENCES public.user_account_(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- TOC entry 4714 (class 2606 OID 18033)
-- Name: brand_manager_ brand_manager_brand_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.brand_manager_
    ADD CONSTRAINT brand_manager_brand_id_fkey FOREIGN KEY (brand_id) REFERENCES public.brand_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4715 (class 2606 OID 18028)
-- Name: brand_manager_ brand_manager_user_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.brand_manager_
    ADD CONSTRAINT brand_manager_user_account_id_fkey FOREIGN KEY (user_account_id) REFERENCES public.user_account_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4708 (class 2606 OID 18038)
-- Name: brand_report_ brand_report_brand_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.brand_report_
    ADD CONSTRAINT brand_report_brand_id_fkey FOREIGN KEY (brand_id) REFERENCES public.brand_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4709 (class 2606 OID 18043)
-- Name: brand_report_ brand_report_reporter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.brand_report_
    ADD CONSTRAINT brand_report_reporter_id_fkey FOREIGN KEY (reporter_id) REFERENCES public.user_account_(id) ON UPDATE CASCADE ON DELETE SET NULL NOT VALID;


--
-- TOC entry 4745 (class 2606 OID 18837)
-- Name: brand_tag_ brand_tag_brand_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.brand_tag_
    ADD CONSTRAINT brand_tag_brand_id_fkey FOREIGN KEY (brand_id) REFERENCES public.brand_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4746 (class 2606 OID 18842)
-- Name: brand_tag_ brand_tag_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.brand_tag_
    ADD CONSTRAINT brand_tag_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tag_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4743 (class 2606 OID 18608)
-- Name: brand_view_ brand_view_brand_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.brand_view_
    ADD CONSTRAINT brand_view_brand_id_fkey FOREIGN KEY (brand_id) REFERENCES public.brand_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4744 (class 2606 OID 18613)
-- Name: brand_view_ brand_view_user_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.brand_view_
    ADD CONSTRAINT brand_view_user_account_id_fkey FOREIGN KEY (user_account_id) REFERENCES public.user_account_(id) ON UPDATE CASCADE ON DELETE SET NULL NOT VALID;


--
-- TOC entry 4737 (class 2606 OID 18402)
-- Name: country_ country_continent_code_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.country_
    ADD CONSTRAINT country_continent_code_fkey FOREIGN KEY (continent_code) REFERENCES public.continent_(code) ON UPDATE CASCADE;


--
-- TOC entry 4738 (class 2606 OID 18827)
-- Name: country_ country_currency_code_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.country_
    ADD CONSTRAINT country_currency_code_fkey FOREIGN KEY (currency_code) REFERENCES public.currency_(code) ON UPDATE CASCADE ON DELETE SET NULL NOT VALID;


--
-- TOC entry 4739 (class 2606 OID 18481)
-- Name: country_dialing_code_ country_dialing_code_alpha_2_code_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.country_dialing_code_
    ADD CONSTRAINT country_dialing_code_alpha_2_code_fkey FOREIGN KEY (alpha_2_code) REFERENCES public.country_(alpha_2_code) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4690 (class 2606 OID 18408)
-- Name: locality_ locality_country_alpha_2_code_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.locality_
    ADD CONSTRAINT locality_country_alpha_2_code_fkey FOREIGN KEY (alpha_2_code) REFERENCES public.country_(alpha_2_code) ON UPDATE CASCADE NOT VALID;


--
-- TOC entry 4694 (class 2606 OID 18135)
-- Name: product_ product_brand_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_
    ADD CONSTRAINT product_brand_id_fkey FOREIGN KEY (brand_id) REFERENCES public.brand_(id) ON UPDATE CASCADE ON DELETE SET NULL NOT VALID;


--
-- TOC entry 4695 (class 2606 OID 18048)
-- Name: product_ product_creator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_
    ADD CONSTRAINT product_creator_id_fkey FOREIGN KEY (creator_id) REFERENCES public.user_account_(id) ON UPDATE CASCADE ON DELETE SET NULL NOT VALID;


--
-- TOC entry 4729 (class 2606 OID 18307)
-- Name: product_edit_history_ product_edit_history_editor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_edit_history_
    ADD CONSTRAINT product_edit_history_editor_id_fkey FOREIGN KEY (editor_id) REFERENCES public.user_account_(id) ON UPDATE CASCADE ON DELETE SET NULL NOT VALID;


--
-- TOC entry 4730 (class 2606 OID 18312)
-- Name: product_edit_history_ product_edit_history_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_edit_history_
    ADD CONSTRAINT product_edit_history_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.product_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4712 (class 2606 OID 18058)
-- Name: product_manager_ product_manager_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_manager_
    ADD CONSTRAINT product_manager_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.product_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4713 (class 2606 OID 18053)
-- Name: product_manager_ product_manager_user_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_manager_
    ADD CONSTRAINT product_manager_user_account_id_fkey FOREIGN KEY (user_account_id) REFERENCES public.user_account_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4696 (class 2606 OID 18737)
-- Name: product_ product_parent_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_
    ADD CONSTRAINT product_parent_product_id_fkey FOREIGN KEY (parent_product_id) REFERENCES public.product_(id) ON UPDATE CASCADE ON DELETE SET NULL NOT VALID;


--
-- TOC entry 4698 (class 2606 OID 18080)
-- Name: product_tag_ product_tag_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_tag_
    ADD CONSTRAINT product_tag_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.product_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4699 (class 2606 OID 18085)
-- Name: product_tag_ product_tag_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_tag_
    ADD CONSTRAINT product_tag_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tag_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4704 (class 2606 OID 18732)
-- Name: product_report_ product_variant_report_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_report_
    ADD CONSTRAINT product_variant_report_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.product_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4705 (class 2606 OID 18105)
-- Name: product_report_ product_variant_report_reporter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_report_
    ADD CONSTRAINT product_variant_report_reporter_id_fkey FOREIGN KEY (reporter_id) REFERENCES public.user_account_(id) ON UPDATE CASCADE ON DELETE SET NULL NOT VALID;


--
-- TOC entry 4702 (class 2606 OID 18727)
-- Name: product_vote_ product_variant_vote_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_vote_
    ADD CONSTRAINT product_variant_vote_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.product_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4703 (class 2606 OID 18115)
-- Name: product_vote_ product_variant_vote_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_vote_
    ADD CONSTRAINT product_variant_vote_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4749 (class 2606 OID 18869)
-- Name: product_view_ product_view_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_view_
    ADD CONSTRAINT product_view_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.product_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4750 (class 2606 OID 18874)
-- Name: product_view_ product_view_user_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_view_
    ADD CONSTRAINT product_view_user_account_id_fkey FOREIGN KEY (user_account_id) REFERENCES public.user_account_(id) ON UPDATE CASCADE ON DELETE SET NULL NOT VALID;


--
-- TOC entry 4687 (class 2606 OID 18120)
-- Name: store_ store_brand_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_
    ADD CONSTRAINT store_brand_id_fkey FOREIGN KEY (brand_id) REFERENCES public.brand_(id) ON UPDATE CASCADE ON DELETE SET NULL NOT VALID;


--
-- TOC entry 4688 (class 2606 OID 18125)
-- Name: store_ store_creator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_
    ADD CONSTRAINT store_creator_id_fkey FOREIGN KEY (creator_id) REFERENCES public.user_account_(id) ON UPDATE CASCADE ON DELETE SET NULL NOT VALID;


--
-- TOC entry 4731 (class 2606 OID 18338)
-- Name: store_edit_history_ store_edit_history_editor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_edit_history_
    ADD CONSTRAINT store_edit_history_editor_id_fkey FOREIGN KEY (editor_id) REFERENCES public.user_account_(id) ON UPDATE CASCADE ON DELETE SET NULL NOT VALID;


--
-- TOC entry 4732 (class 2606 OID 18343)
-- Name: store_edit_history_ store_edit_history_store_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_edit_history_
    ADD CONSTRAINT store_edit_history_store_id_fkey FOREIGN KEY (store_id) REFERENCES public.store_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4689 (class 2606 OID 18130)
-- Name: store_ store_locality_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_
    ADD CONSTRAINT store_locality_id_fkey FOREIGN KEY (locality_id) REFERENCES public.locality_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4692 (class 2606 OID 18145)
-- Name: store_manager_ store_manager_store_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_manager_
    ADD CONSTRAINT store_manager_store_id_fkey FOREIGN KEY (store_id) REFERENCES public.store_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4693 (class 2606 OID 18140)
-- Name: store_manager_ store_manager_user_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_manager_
    ADD CONSTRAINT store_manager_user_account_id_fkey FOREIGN KEY (user_account_id) REFERENCES public.user_account_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4734 (class 2606 OID 18384)
-- Name: store_product_ store_product_creator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_product_
    ADD CONSTRAINT store_product_creator_id_fkey FOREIGN KEY (creator_id) REFERENCES public.user_account_(id) ON UPDATE CASCADE ON DELETE SET NULL NOT VALID;


--
-- TOC entry 4733 (class 2606 OID 18358)
-- Name: store_product_history_ store_product_history_editor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_product_history_
    ADD CONSTRAINT store_product_history_editor_id_fkey FOREIGN KEY (editor_id) REFERENCES public.user_account_(id) ON UPDATE CASCADE ON DELETE SET NULL NOT VALID;


--
-- TOC entry 4735 (class 2606 OID 18722)
-- Name: store_product_ store_product_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_product_
    ADD CONSTRAINT store_product_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.product_(id) ON UPDATE CASCADE ON DELETE SET NULL NOT VALID;


--
-- TOC entry 4736 (class 2606 OID 18374)
-- Name: store_product_ store_product_store_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_product_
    ADD CONSTRAINT store_product_store_id_fkey FOREIGN KEY (store_id) REFERENCES public.store_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4706 (class 2606 OID 18170)
-- Name: store_report_ store_report_reporter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_report_
    ADD CONSTRAINT store_report_reporter_id_fkey FOREIGN KEY (reporter_id) REFERENCES public.user_account_(id) ON UPDATE CASCADE ON DELETE SET NULL NOT VALID;


--
-- TOC entry 4707 (class 2606 OID 18165)
-- Name: store_report_ store_report_store_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_report_
    ADD CONSTRAINT store_report_store_id_fkey FOREIGN KEY (store_id) REFERENCES public.store_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4725 (class 2606 OID 18243)
-- Name: store_shadow_ban_ store_shadow_ban_imposer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_shadow_ban_
    ADD CONSTRAINT store_shadow_ban_imposer_id_fkey FOREIGN KEY (imposer_id) REFERENCES public.user_account_(id) ON UPDATE CASCADE ON DELETE SET NULL NOT VALID;


--
-- TOC entry 4726 (class 2606 OID 18238)
-- Name: store_shadow_ban_ store_shadow_ban_store_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_shadow_ban_
    ADD CONSTRAINT store_shadow_ban_store_id_fkey FOREIGN KEY (store_id) REFERENCES public.store_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4719 (class 2606 OID 18175)
-- Name: store_tag_ store_tag_store_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_tag_
    ADD CONSTRAINT store_tag_store_id_fkey FOREIGN KEY (store_id) REFERENCES public.store_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4720 (class 2606 OID 18180)
-- Name: store_tag_ store_tag_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_tag_
    ADD CONSTRAINT store_tag_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tag_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4747 (class 2606 OID 18853)
-- Name: store_view_ store_view_store_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_view_
    ADD CONSTRAINT store_view_store_id_fkey FOREIGN KEY (store_id) REFERENCES public.store_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4748 (class 2606 OID 18858)
-- Name: store_view_ store_view_user_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.store_view_
    ADD CONSTRAINT store_view_user_account_id_fkey FOREIGN KEY (user_account_id) REFERENCES public.user_account_(id) ON UPDATE CASCADE ON DELETE SET NULL NOT VALID;


--
-- TOC entry 4697 (class 2606 OID 18018)
-- Name: tag_ tag_creator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tag_
    ADD CONSTRAINT tag_creator_id_fkey FOREIGN KEY (creator_id) REFERENCES public.user_account_(id) ON UPDATE CASCADE ON DELETE SET NULL NOT VALID;


--
-- TOC entry 4716 (class 2606 OID 19219)
-- Name: user_account_session_ user_account_session_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_account_session_
    ADD CONSTRAINT user_account_session_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.user_client_(id) ON UPDATE CASCADE ON DELETE SET NULL NOT VALID;


--
-- TOC entry 4717 (class 2606 OID 18457)
-- Name: user_account_session_ user_account_session_os_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_account_session_
    ADD CONSTRAINT user_account_session_os_id_fkey FOREIGN KEY (os_id) REFERENCES public.user_os_(id) ON UPDATE CASCADE ON DELETE SET NULL NOT VALID;


--
-- TOC entry 4721 (class 2606 OID 17973)
-- Name: user_account_ user_account_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_account_
    ADD CONSTRAINT user_account_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4751 (class 2606 OID 18885)
-- Name: user_account_view_ user_account_view_user_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_account_view_
    ADD CONSTRAINT user_account_view_user_account_id_fkey FOREIGN KEY (user_account_id) REFERENCES public.user_account_(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- TOC entry 4752 (class 2606 OID 18890)
-- Name: user_account_view_ user_account_view_viewer_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_account_view_
    ADD CONSTRAINT user_account_view_viewer_account_id_fkey FOREIGN KEY (viewer_account_id) REFERENCES public.user_account_(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- TOC entry 4700 (class 2606 OID 18008)
-- Name: user_account_badge_ user_badge_badge_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_account_badge_
    ADD CONSTRAINT user_badge_badge_id_fkey FOREIGN KEY (badge_id) REFERENCES public.badge_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4701 (class 2606 OID 17978)
-- Name: user_account_badge_ user_badge_user_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_account_badge_
    ADD CONSTRAINT user_badge_user_account_id_fkey FOREIGN KEY (user_account_id) REFERENCES public.user_account_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4740 (class 2606 OID 18538)
-- Name: user_phone_number_ user_phone_number_dialing_code_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_phone_number_
    ADD CONSTRAINT user_phone_number_dialing_code_id_fkey FOREIGN KEY (dialing_code_id) REFERENCES public.country_dialing_code_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4741 (class 2606 OID 18581)
-- Name: user_phone_number_ user_phone_number_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_phone_number_
    ADD CONSTRAINT user_phone_number_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4742 (class 2606 OID 18555)
-- Name: user_phone_number_verification_code_ user_phone_number_verification_code_phone_number_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_phone_number_verification_code_
    ADD CONSTRAINT user_phone_number_verification_code_phone_number_id_fkey FOREIGN KEY (phone_number_id) REFERENCES public.user_phone_number_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4710 (class 2606 OID 17993)
-- Name: user_account_report_ user_report_reporter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_account_report_
    ADD CONSTRAINT user_report_reporter_id_fkey FOREIGN KEY (reporter_account_id) REFERENCES public.user_account_(id) ON UPDATE CASCADE ON DELETE SET NULL NOT VALID;


--
-- TOC entry 4711 (class 2606 OID 17988)
-- Name: user_account_report_ user_report_user_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_account_report_
    ADD CONSTRAINT user_report_user_account_id_fkey FOREIGN KEY (user_account_id) REFERENCES public.user_account_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4718 (class 2606 OID 17998)
-- Name: user_account_session_ user_session_user_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_account_session_
    ADD CONSTRAINT user_session_user_account_id_fkey FOREIGN KEY (user_account_id) REFERENCES public.user_account_(id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- TOC entry 4722 (class 2606 OID 18233)
-- Name: user_shadow_ban_ user_shadow_ban_imposer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_shadow_ban_
    ADD CONSTRAINT user_shadow_ban_imposer_id_fkey FOREIGN KEY (imposer_id) REFERENCES public.user_account_(id) ON UPDATE CASCADE ON DELETE SET NULL NOT VALID;


--
-- TOC entry 4723 (class 2606 OID 18221)
-- Name: user_shadow_ban_ user_shadow_ban_store_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_shadow_ban_
    ADD CONSTRAINT user_shadow_ban_store_id_fkey FOREIGN KEY (store_id) REFERENCES public.store_(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- TOC entry 4724 (class 2606 OID 18216)
-- Name: user_shadow_ban_ user_shadow_ban_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_shadow_ban_
    ADD CONSTRAINT user_shadow_ban_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user_(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- TOC entry 4903 (class 0 OID 0)
-- Dependencies: 5
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: mahouk
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO PUBLIC;


-- Completed on 2023-03-02 08:56:27 +04

--
-- PostgreSQL database dump complete
--

