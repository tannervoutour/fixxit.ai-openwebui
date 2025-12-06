# Supabase Logs Integration Proposal for Fixxit.ai OpenWebUI

**Date**: December 6, 2025  
**Project**: OpenWebUI Supabase Logs Integration  
**Prepared By**: Claude (Sonnet 4)

## Executive Summary

This document proposes a comprehensive integration between OpenWebUI and Supabase for external logs management, featuring group-based database coordination, AI-powered log creation, and enterprise-grade filtering/sorting capabilities.

### Key Objectives
- ✅ **External Log Storage**: Logs stored in Supabase, not OpenWebUI database
- ✅ **Group-based Access**: Users see only logs from their assigned groups
- ✅ **AI-Enhanced Creation**: OpenAI integration for intelligent log insights
- ✅ **Enterprise Features**: Advanced sorting, filtering, and search capabilities
- ✅ **Security**: Robust authentication bridge between OpenWebUI and Supabase

---

## 1. Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   OpenWebUI     │    │   Supabase Logs  │    │     OpenAI API      │
│   Frontend      │◄──►│   Coordination   │◄──►│   (AI Insights)     │
│                 │    │     Layer        │    │                     │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
         │                       │                        
         ▼                       ▼                        
┌─────────────────┐    ┌─────────────────────┐
│   OpenWebUI     │    │   Supabase DBs      │
│   Backend       │    │   (Group-specific)   │
│   (User Groups) │    │   • Ecotex-ABQ DB   │
│                 │    │   • Engineering DB   │
└─────────────────┘    │   • Operations DB    │
                       └─────────────────────┘
```

### 1.2 Technology Stack

**Frontend (Svelte):**
- Enhanced LogsModal with full CRUD functionality
- Data tables with sorting/filtering (SvelteKit patterns)
- Real-time log creation form with AI assistance
- Group-aware UI components

**Backend (Python FastAPI):**
- New `/api/v1/logs` router following OpenWebUI patterns
- Supabase client management with connection pooling
- Group-to-database coordination service
- OpenAI integration for AI insights generation

**External Services:**
- **Supabase**: PostgreSQL databases with Row Level Security
- **OpenAI**: GPT-3.5/GPT-4 for AI insight generation
- **Redis** (optional): Caching for performance optimization

---

## 2. Implementation Strategy

### 2.1 Recommended Approach: Local Database Mapping

**Rationale**: Leverage OpenWebUI's existing group system by storing Supabase configurations in the `group.data` JSON field.

**Benefits**:
- ✅ No database schema changes required
- ✅ Leverages existing group permission system  
- ✅ Flexible per-group configuration
- ✅ Secure configuration storage
- ✅ Incremental implementation possible

### 2.2 Group-to-Database Coordination

```typescript
// Group Supabase Configuration Schema
interface SupabaseGroupConfig {
  url: string;                    // Supabase project URL
  anon_key: string;              // Read-only public key
  service_role_key?: string;     // Admin operations (encrypted)
  table_name: string;            // Default: "logs"
  enabled: boolean;              // Feature toggle
  rate_limit?: number;           // Requests per minute
}

// Stored in existing group.data JSON field
group.data = {
  "supabase": {
    "url": "https://ecotex-abq.supabase.co",
    "anon_key": "eyJ...",
    "service_role_key": "encrypted:...",
    "table_name": "logs", 
    "enabled": true,
    "rate_limit": 100
  }
}
```

---

## 3. Technical Implementation Details

### 3.1 Backend Architecture

#### New API Router: `/backend/open_webui/routers/logs.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from open_webui.utils.auth import get_verified_user
from open_webui.models.groups import Groups
from open_webui.utils.supabase import SupabaseManager
from open_webui.utils.openai import generate_ai_insight

router = APIRouter()
supabase_manager = SupabaseManager()

@router.get("/logs")
async def get_logs(
    user=Depends(get_verified_user),
    category: Optional[str] = None,
    business_impact: Optional[str] = None,
    verified: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_desc: bool = True
):
    """Get logs accessible to user based on group membership"""
    user_groups = Groups.get_groups_by_member_id(user.id)
    all_logs = []
    
    for group in user_groups:
        client = supabase_manager.get_client_for_group(group.id)
        if not client:
            continue
            
        query = client.table("logs").select("*")
        
        # Apply filters
        if category:
            query = query.eq("problem_category", category)
        if business_impact:
            query = query.eq("business_impact", business_impact)
        if verified is not None:
            query = query.eq("verified", verified)
            
        # Apply sorting and pagination
        query = query.order(sort_by, desc=sort_desc)
        query = query.range(offset, offset + limit - 1)
        
        try:
            response = query.execute()
            for log in response.data:
                log["source_group"] = group.name
                log["source_group_id"] = group.id
            all_logs.extend(response.data)
        except Exception as e:
            # Log error but continue with other groups
            logger.error(f"Error fetching logs from group {group.name}: {e}")
    
    # Sort combined results
    if sort_desc:
        all_logs.sort(key=lambda x: x.get(sort_by, ""), reverse=True)
    else:
        all_logs.sort(key=lambda x: x.get(sort_by, ""))
    
    return {
        "logs": all_logs[:limit],
        "total": len(all_logs),
        "has_more": len(all_logs) > limit
    }

@router.post("/logs")
async def create_log(
    log_data: LogCreationRequest,
    group_id: str,
    user=Depends(get_verified_user)
):
    """Create new log with AI-enhanced insights"""
    
    # Verify user access to group
    user_groups = [g.id for g in Groups.get_groups_by_member_id(user.id)]
    if group_id not in user_groups:
        raise HTTPException(status_code=403, detail="Access denied to group")
    
    client = supabase_manager.get_client_for_group(group_id)
    if not client:
        raise HTTPException(status_code=404, detail="Supabase not configured for group")
    
    # Generate AI insights
    ai_insight = await generate_ai_insight(
        title=log_data.insight_title,
        description=log_data.description,
        category=log_data.problem_category,
        equipment=log_data.equipment_involved
    )
    
    # Prepare log data
    log_entry = {
        "session_id": f"openwebui-{uuid.uuid4()}",
        "user_name": user.name,  # From OpenWebUI context
        "insight_title": log_data.insight_title,
        "insight_content": ai_insight.content,
        "ai_model": ai_insight.model,
        "ai_confidence_score": ai_insight.confidence,
        "equipment_involved": log_data.equipment_involved,
        "problem_category": log_data.problem_category,
        "root_cause": log_data.root_cause,
        "business_impact": log_data.business_impact,
        "tags": log_data.tags,
        "source": "openwebui_manual",
        "log_type": "ai_insight",
        "notes": log_data.notes,
        # AI-enhanced fields
        "solution_steps": ai_insight.solution_steps,
        "tools_required": ai_insight.tools_required,
        "reusability_score": ai_insight.reusability_score
    }
    
    try:
        response = client.table("logs").insert(log_entry).execute()
        return {"success": True, "log": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create log: {str(e)}")
```

#### Supabase Connection Manager: `/backend/open_webui/utils/supabase.py`

```python
from supabase import create_client, Client
from typing import Dict, List, Optional
from open_webui.models.groups import Groups
import logging

logger = logging.getLogger(__name__)

class SupabaseManager:
    def __init__(self):
        self._clients: Dict[str, Client] = {}
        self._configs: Dict[str, SupabaseGroupConfig] = {}
    
    def get_client_for_group(self, group_id: str) -> Optional[Client]:
        """Get Supabase client for specific group"""
        if group_id in self._clients:
            return self._clients[group_id]
        
        config = self._get_group_config(group_id)
        if not config or not config.enabled:
            return None
        
        try:
            client = create_client(config.url, config.anon_key)
            self._clients[group_id] = client
            self._configs[group_id] = config
            logger.info(f"Created Supabase client for group {group_id}")
            return client
        except Exception as e:
            logger.error(f"Failed to create Supabase client for group {group_id}: {e}")
            return None
    
    def _get_group_config(self, group_id: str) -> Optional[SupabaseGroupConfig]:
        """Extract Supabase config from group data"""
        group = Groups.get_group_by_id(group_id)
        if not group or not group.data or "supabase" not in group.data:
            return None
        
        try:
            config_data = group.data["supabase"]
            return SupabaseGroupConfig(**config_data)
        except Exception as e:
            logger.error(f"Invalid Supabase config for group {group_id}: {e}")
            return None
    
    def get_user_accessible_groups(self, user_id: str) -> List[tuple]:
        """Get all groups user can access with Supabase configured"""
        user_groups = Groups.get_groups_by_member_id(user_id)
        accessible = []
        
        for group in user_groups:
            client = self.get_client_for_group(group.id)
            if client:
                accessible.append((group.name, group.id, client))
        
        return accessible
    
    def refresh_connections(self):
        """Refresh all client connections (for config updates)"""
        self._clients.clear()
        self._configs.clear()
        logger.info("Refreshed all Supabase connections")

# Global instance
supabase_manager = SupabaseManager()
```

#### OpenAI Integration: `/backend/open_webui/utils/openai_logs.py`

```python
import openai
from typing import Dict, List
from pydantic import BaseModel
import json
import os

class AIInsight(BaseModel):
    content: str
    confidence: float
    model: str
    solution_steps: List[str]
    tools_required: List[str]
    reusability_score: float

async def generate_ai_insight(
    title: str,
    description: str,
    category: str,
    equipment: List[str]
) -> AIInsight:
    """Generate AI-enhanced insights for log entry"""
    
    client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    prompt = f"""
    You are an industrial maintenance expert. Generate a comprehensive insight for this maintenance log:
    
    Title: {title}
    Description: {description}
    Category: {category}
    Equipment: {', '.join(equipment)}
    
    Provide a detailed analysis including:
    1. Comprehensive explanation of the issue/solution
    2. Step-by-step solution approach
    3. Required tools and equipment
    4. Assessment of reusability for similar situations (0.0-1.0)
    5. Your confidence in this analysis (0.0-1.0)
    
    Format as JSON with these fields:
    - insight_content: detailed explanation (2-3 paragraphs)
    - solution_steps: array of step-by-step instructions
    - tools_required: array of tools/equipment needed
    - reusability_score: float 0.0-1.0
    - confidence: float 0.0-1.0
    """
    
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        ai_response = json.loads(response.choices[0].message.content)
        
        return AIInsight(
            content=ai_response["insight_content"],
            confidence=ai_response["confidence"],
            model="gpt-3.5-turbo",
            solution_steps=ai_response["solution_steps"],
            tools_required=ai_response["tools_required"], 
            reusability_score=ai_response["reusability_score"]
        )
        
    except Exception as e:
        logger.error(f"OpenAI insight generation failed: {e}")
        # Fallback to basic insight
        return AIInsight(
            content=f"Log entry for {category}: {description}",
            confidence=0.1,
            model="fallback",
            solution_steps=[],
            tools_required=[],
            reusability_score=0.5
        )
```

### 3.2 Frontend Enhancement

#### Enhanced LogsModal Component

```typescript
// LogsModal.svelte (enhanced)
<script lang="ts">
  import { onMount } from 'svelte';
  import Modal from '$lib/components/common/Modal.svelte';
  import LogsTable from './LogsTable.svelte';
  import LogCreationForm from './LogCreationForm.svelte';
  import LogsFilters from './LogsFilters.svelte';
  
  export let show = false;
  export let onClose = () => {};
  
  let logs = [];
  let loading = false;
  let showCreateForm = false;
  let filters = {
    category: '',
    business_impact: '',
    verified: null,
    sort_by: 'created_at',
    sort_desc: true
  };
  
  onMount(() => {
    if (show) {
      fetchLogs();
    }
  });
  
  async function fetchLogs() {
    loading = true;
    try {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== '' && value !== null) {
          params.append(key, value.toString());
        }
      });
      
      const response = await fetch(`/api/v1/logs?${params}`);
      const data = await response.json();
      logs = data.logs;
    } catch (error) {
      console.error('Error fetching logs:', error);
    } finally {
      loading = false;
    }
  }
  
  function handleFilterChange(newFilters) {
    filters = { ...filters, ...newFilters };
    fetchLogs();
  }
  
  function handleLogCreated() {
    showCreateForm = false;
    fetchLogs(); // Refresh logs
  }
</script>

<Modal size="xl" bind:show>
  <div class="py-3 dark:text-gray-300 text-gray-700">
    <div class="mb-4 flex items-center justify-between">
      <h2 class="text-lg font-semibold flex items-center gap-2">
        <Logs className="size-5" strokeWidth="2" />
        Industrial Logs
      </h2>
      <button
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        on:click={() => showCreateForm = !showCreateForm}
      >
        {showCreateForm ? 'View Logs' : 'Create Log'}
      </button>
    </div>
    
    {#if showCreateForm}
      <LogCreationForm onCreated={handleLogCreated} onCancel={() => showCreateForm = false} />
    {:else}
      <LogsFilters {filters} onChange={handleFilterChange} />
      
      {#if loading}
        <div class="text-center py-8">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p class="mt-2 text-sm text-gray-500">Loading logs...</p>
        </div>
      {:else}
        <LogsTable {logs} onFilterChange={handleFilterChange} />
      {/if}
    {/if}
  </div>
</Modal>
```

#### User Input Form Component

```typescript
// LogCreationForm.svelte
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  
  const dispatch = createEventDispatcher();
  
  let formData = {
    insight_title: '',
    problem_category: '',
    equipment_involved: [],
    description: '',
    business_impact: 'medium',
    root_cause: '',
    tags: [],
    notes: ''
  };
  
  let loading = false;
  let selectedGroup = '';
  let userGroups = [];
  
  const categories = [
    'Preventive Maintenance',
    'Equipment Failure', 
    'Safety Issue',
    'Process Optimization',
    'Emergency Repair',
    'Quality Control',
    'Environmental Compliance'
  ];
  
  onMount(async () => {
    // Fetch user's accessible groups
    const response = await fetch('/api/v1/groups/accessible-with-logs');
    userGroups = await response.json();
    if (userGroups.length > 0) {
      selectedGroup = userGroups[0].id;
    }
  });
  
  async function handleSubmit() {
    if (!formData.insight_title || !formData.description || !selectedGroup) {
      alert('Please fill in all required fields');
      return;
    }
    
    loading = true;
    try {
      const response = await fetch('/api/v1/logs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          group_id: selectedGroup
        })
      });
      
      if (response.ok) {
        dispatch('created');
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      alert('Failed to create log');
    } finally {
      loading = false;
    }
  }
</script>

<div class="space-y-6">
  <h3 class="text-lg font-medium">Create New Log Entry</h3>
  
  <!-- Group Selection -->
  <div>
    <label class="block text-sm font-medium mb-2">Target Group</label>
    <select bind:value={selectedGroup} class="w-full p-2 border rounded-lg">
      {#each userGroups as group}
        <option value={group.id}>{group.name}</option>
      {/each}
    </select>
  </div>
  
  <!-- Essential Fields -->
  <div>
    <label class="block text-sm font-medium mb-2">Title *</label>
    <input 
      bind:value={formData.insight_title}
      maxlength="500"
      class="w-full p-2 border rounded-lg" 
      placeholder="Brief descriptive title"
    />
  </div>
  
  <div class="grid grid-cols-2 gap-4">
    <div>
      <label class="block text-sm font-medium mb-2">Category *</label>
      <select bind:value={formData.problem_category} class="w-full p-2 border rounded-lg">
        <option value="">Select category...</option>
        {#each categories as category}
          <option value={category}>{category}</option>
        {/each}
      </select>
    </div>
    
    <div>
      <label class="block text-sm font-medium mb-2">Business Impact</label>
      <select bind:value={formData.business_impact} class="w-full p-2 border rounded-lg">
        <option value="low">Low</option>
        <option value="medium">Medium</option>
        <option value="high">High</option>
        <option value="critical">Critical</option>
      </select>
    </div>
  </div>
  
  <div>
    <label class="block text-sm font-medium mb-2">Equipment Involved *</label>
    <input 
      bind:value={equipmentInput}
      on:keydown={handleEquipmentInput}
      class="w-full p-2 border rounded-lg" 
      placeholder="Type equipment name and press Enter"
    />
    <div class="mt-2 flex flex-wrap gap-2">
      {#each formData.equipment_involved as equipment, index}
        <span class="px-2 py-1 bg-blue-100 rounded-full text-sm flex items-center gap-1">
          {equipment}
          <button on:click={() => removeEquipment(index)} class="text-red-500">×</button>
        </span>
      {/each}
    </div>
  </div>
  
  <div>
    <label class="block text-sm font-medium mb-2">Description *</label>
    <textarea 
      bind:value={formData.description}
      rows="4"
      class="w-full p-2 border rounded-lg" 
      placeholder="Describe the issue, solution, or insight. AI will enhance this into a comprehensive report."
    ></textarea>
  </div>
  
  <!-- Optional Fields (collapsible) -->
  <details class="border rounded-lg p-3">
    <summary class="cursor-pointer font-medium">Additional Details (Optional)</summary>
    <div class="mt-4 space-y-4">
      <div>
        <label class="block text-sm font-medium mb-2">Root Cause</label>
        <textarea bind:value={formData.root_cause} rows="2" class="w-full p-2 border rounded-lg"></textarea>
      </div>
      
      <div>
        <label class="block text-sm font-medium mb-2">Tags</label>
        <input 
          bind:value={tagsInput}
          on:keydown={handleTagsInput}
          class="w-full p-2 border rounded-lg" 
          placeholder="Add tags (press Enter)"
        />
        <div class="mt-2 flex flex-wrap gap-2">
          {#each formData.tags as tag, index}
            <span class="px-2 py-1 bg-green-100 rounded-full text-sm flex items-center gap-1">
              {tag}
              <button on:click={() => removeTag(index)} class="text-red-500">×</button>
            </span>
          {/each}
        </div>
      </div>
      
      <div>
        <label class="block text-sm font-medium mb-2">Additional Notes</label>
        <textarea bind:value={formData.notes} rows="3" class="w-full p-2 border rounded-lg"></textarea>
      </div>
    </div>
  </details>
  
  <!-- Action Buttons -->
  <div class="flex gap-3 pt-4">
    <button
      on:click={handleSubmit}
      disabled={loading}
      class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
    >
      {#if loading}
        <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
      {/if}
      Create Log with AI Enhancement
    </button>
    
    <button
      on:click={() => dispatch('cancel')}
      class="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
    >
      Cancel
    </button>
  </div>
</div>
```

---

## 4. Security Considerations

### 4.1 Authentication Bridge
- **User Context**: OpenWebUI user information passed to Supabase logs
- **Group Verification**: Server-side validation of user's group membership
- **API Keys**: Encrypted storage of Supabase service keys in database
- **Rate Limiting**: Per-group and per-user rate limits on log operations

### 4.2 Data Security
- **Supabase RLS**: Row Level Security policies for additional data protection
- **Audit Logging**: All cross-database operations logged in OpenWebUI audit system
- **Input Validation**: Strict validation of all user inputs and AI-generated content
- **Error Handling**: No sensitive information in error responses

### 4.3 Access Control
- **Group-based Access**: Users only see logs from their assigned groups
- **Admin Controls**: Group admins can configure Supabase connections
- **Read-only Default**: Default to read-only access, separate permissions for write operations

---

## 5. Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)
**Deliverables:**
- ✅ Backend logs router with basic CRUD operations
- ✅ Supabase connection manager 
- ✅ Group configuration system
- ✅ Basic frontend logs table with viewing capability

**Success Criteria:**
- Users can view logs from their group's Supabase database
- Proper error handling for connection failures
- Basic filtering by category and date

### Phase 2: AI Integration (Week 3)
**Deliverables:**
- ✅ OpenAI integration for insight generation
- ✅ Log creation form with user input validation
- ✅ AI confidence scoring and fallback handling

**Success Criteria:**
- Users can create logs with AI-enhanced insights
- Proper handling of OpenAI API failures
- Quality AI-generated content with confidence scoring

### Phase 3: Advanced Features (Week 4)
**Deliverables:**
- ✅ Advanced sorting and filtering
- ✅ Tag-based search and auto-completion
- ✅ Export functionality
- ✅ Real-time updates (optional)

**Success Criteria:**
- Comprehensive search and filter capabilities
- Responsive UI for large log datasets
- Export to multiple formats (JSON, CSV)

### Phase 4: Production & Optimization (Week 5)
**Deliverables:**
- ✅ Performance optimization and caching
- ✅ Enhanced error handling and monitoring
- ✅ Security audit and testing
- ✅ Documentation and training materials

**Success Criteria:**
- Production-ready performance
- Comprehensive error monitoring
- Security validation complete

---

## 6. Risk Assessment & Mitigation

### High-Risk Items
1. **Supabase Connection Failures**
   - *Mitigation*: Robust error handling, connection pooling, fallback mechanisms
   
2. **OpenAI API Costs**
   - *Mitigation*: Rate limiting, efficient prompts, fallback to basic logs
   
3. **Group Configuration Complexity**
   - *Mitigation*: Intuitive admin interface, comprehensive validation, clear documentation

### Medium-Risk Items
1. **Performance with Large Datasets**
   - *Mitigation*: Pagination, indexes, client-side virtual scrolling
   
2. **Authentication Edge Cases**
   - *Mitigation*: Comprehensive testing, clear error messages, audit logging

---

## 7. Success Metrics

### Technical Metrics
- **Response Time**: < 2 seconds for log queries
- **Availability**: 99.9% uptime for log access
- **Error Rate**: < 1% of API calls fail

### User Experience Metrics
- **Load Time**: Initial logs view < 3 seconds
- **Search Performance**: Results in < 1 second
- **AI Quality**: > 85% user satisfaction with AI insights

### Business Metrics
- **User Adoption**: > 80% of users create at least one log within 30 days
- **Log Creation Rate**: Average 2+ logs per active user per week
- **Search Usage**: > 50% of users use advanced filtering

---

## 8. Dependencies & Requirements

### External Dependencies
- **OpenAI API Access**: Required for AI insight generation
- **Supabase Projects**: Pre-configured for each group
- **Redis**: Optional but recommended for caching

### OpenWebUI Requirements
- **Groups System**: Functional group membership system
- **Authentication**: Working JWT-based auth
- **FastAPI Version**: Compatible with async operations

### Configuration Requirements
- Environment variables for OpenAI API key
- Group-level Supabase configuration
- Rate limiting and timeout configurations

---

## 9. Conclusion & Next Steps

This proposal provides a comprehensive approach to integrating Supabase logs with OpenWebUI while maintaining security, performance, and user experience standards. The phased implementation approach minimizes risk while delivering value incrementally.

### Immediate Next Steps
1. **Approval & Resource Allocation**: Confirm development timeline and resources
2. **Environment Setup**: Configure development Supabase instances for testing
3. **API Key Procurement**: Obtain OpenAI API access for AI features
4. **Development Kickoff**: Begin Phase 1 implementation

### Expected Outcomes
- Seamless integration between OpenWebUI and external Supabase logs
- Enhanced user experience with AI-powered log creation
- Enterprise-grade filtering, sorting, and search capabilities
- Robust group-based access control maintaining security requirements

The proposed architecture leverages OpenWebUI's existing strengths while adding powerful external log management capabilities that will significantly enhance the Fixxit.ai platform's value proposition for industrial maintenance teams.

---

**Document Version**: 1.0  
**Prepared By**: Claude (Sonnet 4)  
**Date**: December 6, 2025