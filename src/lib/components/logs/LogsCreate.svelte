<script lang="ts">
	import { getContext, createEventDispatcher } from 'svelte';
	import { toast } from 'svelte-sonner';
	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	import Spinner from '$lib/components/common/Spinner.svelte';
	import { createLog } from '$lib/apis/logs';

	export let availableGroups = [];
	export let problemCategories = [];
	export let availableEquipment = [];

	let submitting = false;
	let selectedGroupId = '';

	// Problem category management
	let showNewCategoryInput = false;
	let newCategoryValue = '';

	// Log creation form
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

	// Set default group
	$: if (availableGroups.length > 0 && !selectedGroupId) {
		selectedGroupId = availableGroups[0].id;
	}

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
		selectedGroupId = availableGroups.length > 0 ? availableGroups[0].id : '';
		showNewCategoryInput = false;
		newCategoryValue = '';
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

	const handleCategoryChange = (value) => {
		if (value === '_new_category') {
			showNewCategoryInput = true;
			formData.problem_category = '';
		} else {
			showNewCategoryInput = false;
			formData.problem_category = value;
		}
	};

	const handleNewCategorySubmit = () => {
		if (newCategoryValue.trim()) {
			formData.problem_category = newCategoryValue.trim();
			showNewCategoryInput = false;
			newCategoryValue = '';
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
				solution_steps: formData.solution_steps.filter((step) => step.trim() !== ''),
				tools_required: formData.tools_required.filter((tool) => tool.trim() !== ''),
				tags: formData.tags.filter((tag) => tag.trim() !== ''),
				equipment_group: formData.equipment_group.filter((eq) => eq.trim() !== '')
			};

			const result = await createLog(localStorage.token, selectedGroupId, cleanedFormData);

			if (result && result.success) {
				toast.success($i18n.t('Log created successfully'));
				resetForm();
				dispatch('log-created');
			}
		} catch (error) {
			console.error('Error creating log:', error);
			toast.error($i18n.t('Error creating log: ') + (error.message || error));
		} finally {
			submitting = false;
		}
	};
</script>

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

			{#if showNewCategoryInput}
				<!-- New Category Input -->
				<div class="space-y-2">
					<div class="flex items-center space-x-2">
						<input
							type="text"
							bind:value={newCategoryValue}
							placeholder={$i18n.t('Enter new category name')}
							class="flex-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2"
							on:keydown={(e) => e.key === 'Enter' && handleNewCategorySubmit()}
						/>
						<button
							type="button"
							on:click={handleNewCategorySubmit}
							class="px-3 py-2 text-sm bg-green-600 text-white rounded hover:bg-green-700"
						>
							{$i18n.t('Add')}
						</button>
						<button
							type="button"
							on:click={() => {
								showNewCategoryInput = false;
								newCategoryValue = '';
							}}
							class="px-3 py-2 text-sm bg-gray-500 text-white rounded hover:bg-gray-600"
						>
							{$i18n.t('Cancel')}
						</button>
					</div>
				</div>
			{:else}
				<!-- Category Dropdown -->
				<div class="space-y-2">
					<select
						value={formData.problem_category}
						on:change={(e) => handleCategoryChange(e.target.value)}
						class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2"
					>
						<option value="">{$i18n.t('Select category')}</option>
						{#each problemCategories as category}
							<option value={category}>{category}</option>
						{/each}
						<option value="_new_category" class="italic text-blue-600 dark:text-blue-400">
							+ {$i18n.t('Add new category')}
						</option>
					</select>

					{#if formData.problem_category}
						<div class="text-xs text-gray-600 dark:text-gray-400">
							{$i18n.t('Selected')}: <span class="font-medium">{formData.problem_category}</span>
						</div>
					{/if}
				</div>
			{/if}
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
				disabled={submitting ||
					!formData.insight_title.trim() ||
					!formData.insight_content.trim()}
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
