<script lang="ts">
	import { getContext } from 'svelte';
	const i18n = getContext('i18n');

	export let selectedCategory = '';
	export let verifiedFilter = '';
	export let equipmentFilter = '';
	export let sortBy = 'created_at';
	export let dateRangeAfter = '';
	export let dateRangeBefore = '';
	export let selectedUser = '';
	export let titleSearch = '';
	export let categories = [];
</script>

<div class="p-6 bg-gray-50 dark:bg-gray-800 rounded-lg space-y-4">
	<!-- Primary Filters Row -->
	<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
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

	<!-- Advanced Filters Row (Conditional) -->
	{#if sortBy === 'created_at' || sortBy === 'updated_at'}
		<div
			class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700"
		>
			<div>
				<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
					{$i18n.t('After Date')}
				</label>
				<input
					type="date"
					bind:value={dateRangeAfter}
					class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-1.5 text-sm"
				/>
			</div>
			<div>
				<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
					{$i18n.t('Before Date')}
				</label>
				<input
					type="date"
					bind:value={dateRangeBefore}
					class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-1.5 text-sm"
				/>
			</div>
		</div>
	{/if}

	{#if sortBy === 'user_name'}
		<div class="pt-4 border-t border-gray-200 dark:border-gray-700">
			<div class="max-w-md">
				<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
					{$i18n.t('Select User')}
				</label>
				<input
					type="text"
					bind:value={selectedUser}
					placeholder={$i18n.t('Enter username to filter')}
					class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-1.5 text-sm"
				/>
			</div>
		</div>
	{/if}

	{#if sortBy === 'insight_title'}
		<div class="pt-4 border-t border-gray-200 dark:border-gray-700">
			<div class="max-w-md">
				<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
					{$i18n.t('Search Title')}
				</label>
				<input
					type="text"
					bind:value={titleSearch}
					placeholder={$i18n.t('Enter title keywords')}
					class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-1.5 text-sm"
				/>
			</div>
		</div>
	{/if}
</div>
