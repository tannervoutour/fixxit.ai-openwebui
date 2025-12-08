<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	const i18n = getContext('i18n');

	import Modal from '$lib/components/common/Modal.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Logs from '../icons/Logs.svelte';
	import { getLogs, createLog, getProblemCategories, getEquipmentGroups, getGroupsWithLogs } from '$lib/apis/logs';

	export let show = false;
	export let onClose = () => {};

	// Modal state
	let selectedTab: 'view' | 'create' = 'view';
	let loading = false;
	let submitting = false;

	// Logs viewing state
	let logs = [];
	let categories = [];
	let totalLogs = 0;
	let hasMore = false;

	// Filtering state
	let selectedCategory = '';
	let selectedBusinessImpact = '';
	let verifiedFilter: string = '';
	let equipmentFilter = '';
	let sortBy = 'created_at';
	let sortDesc = true;

	// Available groups and equipment
	let availableGroups = [];
	let availableEquipment = [];
	let problemCategories = [];

	// Log creation form
	let selectedGroupId = '';
	let formData = {
		insight_title: '',
		insight_content: '',
		problem_category: '',
		root_cause: '',
		solution_steps: [''],
		tools_required: [''],
		tags: [''],
		equipment_group: [''],
		notes: ''
	};

	// Helper functions
	const addFormArrayItem = (field: string) => {
		formData[field] = [...formData[field], ''];
	};

	const removeFormArrayItem = (field: string, index: number) => {
		formData[field] = formData[field].filter((_, i) => i !== index);
		if (formData[field].length === 0) {
			formData[field] = [''];
		}
	};

	const updateFormArrayItem = (field: string, index: number, value: string) => {
		formData[field][index] = value;
	};

	const resetForm = () => {
		selectedGroupId = '';
		formData = {
			insight_title: '',
			insight_content: '',
			problem_category: '',
			root_cause: '',
			solution_steps: [''],
			tools_required: [''],
			tags: [''],
			equipment_group: [''],
			notes: ''
		};
	};

	const loadInitialData = async () => {
		try {
			loading = true;
			
			// Load groups with database configured
			const groupsResponse = await getGroupsWithLogs(localStorage.token);
			if (groupsResponse) {
				availableGroups = groupsResponse;
				if (availableGroups.length > 0) {
					selectedGroupId = availableGroups[0].id;
				}
			}

			// Load problem categories
			const categoriesResponse = await getProblemCategories(localStorage.token);
			if (categoriesResponse) {
				problemCategories = categoriesResponse;
			}

			// Load equipment groups
			const equipmentResponse = await getEquipmentGroups(localStorage.token);
			if (equipmentResponse) {
				availableEquipment = equipmentResponse;
			}

			// Load initial logs
			await loadLogs();
			
		} catch (error) {
			console.error('Error loading initial data:', error);
			toast.error($i18n.t('Error loading logs data'));
		} finally {
			loading = false;
		}
	};

	const loadLogs = async () => {
		try {
			loading = true;
			
			const params = {
				limit: 20,
				offset: 0,
				sort_by: sortBy,
				sort_desc: sortDesc
			};

			if (selectedCategory) params.category = selectedCategory;
			if (selectedBusinessImpact) params.business_impact = selectedBusinessImpact;
			if (verifiedFilter !== '') params.verified = verifiedFilter === 'true';
			if (equipmentFilter) params.equipment = equipmentFilter;

			const response = await getLogs(localStorage.token, params);
			
			if (response) {
				logs = response.logs;
				totalLogs = response.total;
				hasMore = response.has_more;
				categories = response.categories;
			}
			
		} catch (error) {
			console.error('Error loading logs:', error);
			toast.error($i18n.t('Error loading logs'));
		} finally {
			loading = false;
		}
	};

	const handleCreateLog = async () => {
		if (!selectedGroupId) {
			toast.error($i18n.t('Please select a group'));
			return;
		}

		if (!formData.insight_title.trim() || !formData.insight_content.trim()) {
			toast.error($i18n.t('Title and content are required'));
			return;
		}

		try {
			submitting = true;

			// Clean up array fields - remove empty strings
			const cleanedFormData = {
				...formData,
				solution_steps: formData.solution_steps.filter(step => step.trim() !== ''),
				tools_required: formData.tools_required.filter(tool => tool.trim() !== ''),
				tags: formData.tags.filter(tag => tag.trim() !== ''),
				equipment_group: formData.equipment_group.filter(eq => eq.trim() !== '')
			};

			const result = await createLog(localStorage.token, selectedGroupId, cleanedFormData);
			
			if (result && result.success) {
				toast.success($i18n.t('Log created successfully'));
				resetForm();
				selectedTab = 'view';
				await loadLogs(); // Refresh the logs list
			}
			
		} catch (error) {
			console.error('Error creating log:', error);
			toast.error($i18n.t('Error creating log: ') + (error.message || error));
		} finally {
			submitting = false;
		}
	};

	const formatDate = (dateString: string) => {
		return new Date(dateString).toLocaleString();
	};

	// Load data when modal opens
	$: if (show) {
		loadInitialData();
	}

	// Reload logs when filters change
	$: if (show && (selectedCategory || selectedBusinessImpact || verifiedFilter || equipmentFilter || sortBy !== 'created_at' || !sortDesc)) {
		loadLogs();
	}
</script>

<Modal size="xl" bind:show>
	<div class="py-3 dark:text-gray-300 text-gray-700">
		<div class="mb-4 flex items-center justify-between">
			<div class="flex items-center space-x-3">
				<Logs className="size-5" strokeWidth="2" />
				<h2 class="text-lg font-semibold">{$i18n.t('Logs')}</h2>
			</div>
		</div>
		
		<!-- Tab Navigation -->
		<div class="flex border-b border-gray-200 dark:border-gray-700 mb-4">
			<button
				class="px-4 py-2 text-sm font-medium border-b-2 {selectedTab === 'view' 
					? 'border-blue-500 text-blue-600 dark:text-blue-400' 
					: 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'}"
				on:click={() => selectedTab = 'view'}
			>
				{$i18n.t('View Logs')}
			</button>
			
			{#if availableGroups.length > 0}
				<button
					class="px-4 py-2 text-sm font-medium border-b-2 {selectedTab === 'create' 
						? 'border-blue-500 text-blue-600 dark:text-blue-400' 
						: 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'}"
					on:click={() => selectedTab = 'create'}
				>
					{$i18n.t('Create Log')}
				</button>
			{/if}
		</div>

		{#if selectedTab === 'view'}
			<!-- View Logs Tab -->
			<div class="space-y-4">
				<!-- Filters -->
				<div class="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
					<div>
						<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
							{$i18n.t('Category')}
						</label>
						<select 
							bind:value={selectedCategory}
							class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-1.5 text-sm"
						>
							<option value="">{$i18n.t('All Categories')}</option>
							{#each categories as category}
								<option value={category}>{category}</option>
							{/each}
						</select>
					</div>
					
					<div>
						<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
							{$i18n.t('Verified')}
						</label>
						<select 
							bind:value={verifiedFilter}
							class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-1.5 text-sm"
						>
							<option value="">{$i18n.t('All')}</option>
							<option value="true">{$i18n.t('Verified')}</option>
							<option value="false">{$i18n.t('Unverified')}</option>
						</select>
					</div>

					<div>
						<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
							{$i18n.t('Sort By')}
						</label>
						<select 
							bind:value={sortBy}
							class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-1.5 text-sm"
						>
							<option value="created_at">{$i18n.t('Date Created')}</option>
							<option value="updated_at">{$i18n.t('Date Updated')}</option>
							<option value="insight_title">{$i18n.t('Title')}</option>
							<option value="user_name">{$i18n.t('User')}</option>
						</select>
					</div>
				</div>

				<!-- Logs List -->
				{#if loading}
					<div class="flex justify-center py-8">
						<Spinner className="size-6" />
					</div>
				{:else if logs.length === 0}
					<div class="text-center py-8 text-gray-500 dark:text-gray-400">
						<Logs className="size-12 mx-auto opacity-50 mb-4" strokeWidth="1.5" />
						<p class="text-lg font-medium mb-2">{$i18n.t('No logs found')}</p>
						<p class="text-sm">
							{availableGroups.length === 0 
								? $i18n.t('No groups with database configuration found')
								: $i18n.t('No logs match your current filters')}
						</p>
					</div>
				{:else}
					<div class="space-y-3 max-h-96 overflow-y-auto">
						{#each logs as log}
							<div class="p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800">
								<div class="flex items-start justify-between mb-2">
									<h3 class="font-medium text-gray-900 dark:text-gray-100">{log.insight_title}</h3>
									<div class="flex items-center space-x-2">
										{#if log.verified}
											<span class="inline-flex items-center px-2 py-1 text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 rounded">
												{$i18n.t('Verified')}
											</span>
										{/if}
										{#if log.problem_category}
											<span class="inline-flex items-center px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 rounded">
												{log.problem_category}
											</span>
										{/if}
									</div>
								</div>
								
								<p class="text-sm text-gray-600 dark:text-gray-300 mb-2 line-clamp-2">{log.insight_content}</p>
								
								<div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
									<span>{$i18n.t('By')} {log.user_name}</span>
									<span>{formatDate(log.created_at)}</span>
								</div>

								{#if log.source_group_name}
									<div class="mt-2 text-xs text-gray-500 dark:text-gray-400">
										{$i18n.t('Group')}: {log.source_group_name}
									</div>
								{/if}
							</div>
						{/each}
					</div>

					{#if hasMore}
						<div class="text-center pt-4">
							<button
								class="px-4 py-2 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
								on:click={loadLogs}
								disabled={loading}
							>
								{loading ? $i18n.t('Loading...') : $i18n.t('Load More')}
							</button>
						</div>
					{/if}
				{/if}
			</div>

		{:else}
			<!-- Create Log Tab -->
			<div class="space-y-4">
				{#if availableGroups.length === 0}
					<div class="text-center py-8 text-gray-500 dark:text-gray-400">
						<p class="text-lg font-medium mb-2">{$i18n.t('No Database Groups Available')}</p>
						<p class="text-sm">
							{$i18n.t('Please configure a database for at least one group to create logs.')}
						</p>
					</div>
				{:else}
					<!-- Group Selection -->
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							{$i18n.t('Select Group')} <span class="text-red-500">*</span>
						</label>
						<select 
							bind:value={selectedGroupId}
							class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2"
							required
						>
							{#each availableGroups as group}
								<option value={group.id}>{group.name}</option>
							{/each}
						</select>
					</div>

					<!-- Title -->
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							{$i18n.t('Log Title')} <span class="text-red-500">*</span>
						</label>
						<input
							type="text"
							bind:value={formData.insight_title}
							placeholder={$i18n.t('Brief descriptive title for this log entry')}
							class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2"
							required
						/>
					</div>

					<!-- Content -->
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							{$i18n.t('Log Content')} <span class="text-red-500">*</span>
						</label>
						<textarea
							bind:value={formData.insight_content}
							rows="4"
							placeholder={$i18n.t('Detailed description of the issue, findings, or insights')}
							class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2"
							required
						></textarea>
					</div>

					<!-- Problem Category -->
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							{$i18n.t('Problem Category')}
						</label>
						<select 
							bind:value={formData.problem_category}
							class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2"
						>
							<option value="">{$i18n.t('Select category')}</option>
							{#each problemCategories as category}
								<option value={category}>{category}</option>
							{/each}
						</select>
					</div>

					<!-- Root Cause -->
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							{$i18n.t('Root Cause')}
						</label>
						<textarea
							bind:value={formData.root_cause}
							rows="2"
							placeholder={$i18n.t('Identified root cause of the issue')}
							class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2"
						></textarea>
					</div>

					<!-- Solution Steps -->
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							{$i18n.t('Solution Steps')}
						</label>
						{#each formData.solution_steps as step, index}
							<div class="flex items-center space-x-2 mb-2">
								<input
									type="text"
									bind:value={step}
									placeholder={$i18n.t('Solution step')} 
									class="flex-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2"
									on:input={(e) => updateFormArrayItem('solution_steps', index, e.target.value)}
								/>
								{#if formData.solution_steps.length > 1}
									<button
										type="button"
										on:click={() => removeFormArrayItem('solution_steps', index)}
										class="px-2 py-2 text-red-600 hover:text-red-800"
									>
										×
									</button>
								{/if}
							</div>
						{/each}
						<button
							type="button"
							on:click={() => addFormArrayItem('solution_steps')}
							class="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
						>
							+ {$i18n.t('Add step')}
						</button>
					</div>

					<!-- Tools Required -->
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							{$i18n.t('Tools Required')}
						</label>
						{#each formData.tools_required as tool, index}
							<div class="flex items-center space-x-2 mb-2">
								<input
									type="text"
									bind:value={tool}
									placeholder={$i18n.t('Tool or equipment needed')}
									class="flex-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2"
									on:input={(e) => updateFormArrayItem('tools_required', index, e.target.value)}
								/>
								{#if formData.tools_required.length > 1}
									<button
										type="button"
										on:click={() => removeFormArrayItem('tools_required', index)}
										class="px-2 py-2 text-red-600 hover:text-red-800"
									>
										×
									</button>
								{/if}
							</div>
						{/each}
						<button
							type="button"
							on:click={() => addFormArrayItem('tools_required')}
							class="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
						>
							+ {$i18n.t('Add tool')}
						</button>
					</div>

					<!-- Equipment Group -->
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							{$i18n.t('Equipment Involved')}
						</label>
						{#each formData.equipment_group as equipment, index}
							<div class="flex items-center space-x-2 mb-2">
								<select
									bind:value={equipment}
									class="flex-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2"
									on:change={(e) => updateFormArrayItem('equipment_group', index, e.target.value)}
								>
									<option value="">{$i18n.t('Select equipment')}</option>
									{#each availableEquipment as eq}
										<option value={eq.conventional_name}>{eq.conventional_name}</option>
									{/each}
								</select>
								{#if formData.equipment_group.length > 1}
									<button
										type="button"
										on:click={() => removeFormArrayItem('equipment_group', index)}
										class="px-2 py-2 text-red-600 hover:text-red-800"
									>
										×
									</button>
								{/if}
							</div>
						{/each}
						<button
							type="button"
							on:click={() => addFormArrayItem('equipment_group')}
							class="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
						>
							+ {$i18n.t('Add equipment')}
						</button>
					</div>

					<!-- Tags -->
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							{$i18n.t('Tags')} <span class="text-xs text-gray-500">(max 3)</span>
						</label>
						{#each formData.tags as tag, index}
							<div class="flex items-center space-x-2 mb-2">
								<input
									type="text"
									bind:value={tag}
									placeholder={$i18n.t('Classification tag')}
									class="flex-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2"
									on:input={(e) => updateFormArrayItem('tags', index, e.target.value)}
								/>
								{#if formData.tags.length > 1}
									<button
										type="button"
										on:click={() => removeFormArrayItem('tags', index)}
										class="px-2 py-2 text-red-600 hover:text-red-800"
									>
										×
									</button>
								{/if}
							</div>
						{/each}
						{#if formData.tags.length < 3}
							<button
								type="button"
								on:click={() => addFormArrayItem('tags')}
								class="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
							>
								+ {$i18n.t('Add tag')}
							</button>
						{/if}
					</div>

					<!-- Notes -->
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							{$i18n.t('Additional Notes')}
						</label>
						<textarea
							bind:value={formData.notes}
							rows="2"
							placeholder={$i18n.t('Any additional notes or observations')}
							class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2"
						></textarea>
					</div>

					<!-- Submit Button -->
					<div class="flex justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
						<button
							type="button"
							on:click={resetForm}
							class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100"
							disabled={submitting}
						>
							{$i18n.t('Reset')}
						</button>
						<button
							type="button"
							on:click={handleCreateLog}
							disabled={submitting || !formData.insight_title.trim() || !formData.insight_content.trim()}
							class="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
						>
							{#if submitting}
								<Spinner className="size-4" />
								<span>{$i18n.t('Creating...')}</span>
							{:else}
								<span>{$i18n.t('Create Log')}</span>
							{/if}
						</button>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</Modal>