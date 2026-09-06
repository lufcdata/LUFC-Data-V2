import React,{useEffect,useMemo,useState}from'react';
import{supabase,supabaseConfigError}from'./supabase';
import{researchUpcomingFixture}from'./statPackFixtureResearch';
import{matchesExactFixtureScope}from'./statPackFixtureScope';
import{canonicalStadiumKey,matchesAtPhysicalStadium}from'./stadiumIdentity';

// RESTORE_FROM_BLOB_REQUIRED
