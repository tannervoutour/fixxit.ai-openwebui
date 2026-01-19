<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { slide } from 'svelte/transition';
	import { quintOut } from 'svelte/easing';
	import { toast } from 'svelte-sonner';
	import { getContext } from 'svelte';

	import { getEquipmentGroups, getGroupsWithLogs } from '$lib/apis/logs';
	import ChevronUp from '../../icons/ChevronUp.svelte';
	import ChevronDown from '../../icons/ChevronDown.svelte';
	import Spinner from '../../common/Spinner.svelte';

	const i18n = getContext('i18n');

	// Props
	export let onSelect: (machineName: string) => void;
	export let className: string = '';

	// State
	let open = false;
	let userGroups = [];
	let selectedGroupId = '';
	let equipmentList = [];
	let loading = false;
	let error = null;
	let containerElement: HTMLElement;

	// Load groups on mount
	onMount(async () => {
		try {
			userGroups = await getGroupsWithLogs(localStorage.token);
			if (userGroups.length > 0) {
				selectedGroupId = userGroups[0].id; // Default to first group
			}
		} catch (e) {
			console.error('Failed to load groups:', e);
			toast.error($i18n.t('Failed to load groups'));
			error = e;
		}
	});

	// Reactive: Load equipment when group changes
	$: if (selectedGroupId) {
		loadEquipment(selectedGroupId);
	}

	const loadEquipment = async (groupId: string) => {
		try {
			loading = true;
			error = null;
			equipmentList = await getEquipmentGroups(localStorage.token, groupId);
		} catch (e) {
			console.error('Failed to load equipment:', e);
			toast.error($i18n.t('Failed to load machines'));
			error = e;
			equipmentList = [];
		} finally {
			loading = false;
		}
	};

	// Click outside handler
	const handleClickOutside = (event: MouseEvent) => {
		if (open && containerElement && !containerElement.contains(event.target as Node)) {
			open = false;
		}
	};

	onMount(() => {
		document.addEventListener('click', handleClickOutside);
	});

	onDestroy(() => {
		document.removeEventListener('click', handleClickOutside);
	});

	// Keyboard support
	const handleKeyDown = (e: KeyboardEvent) => {
		if (e.key === 'Escape' && open) {
			open = false;
			e.preventDefault();
		}
	};

	// Machine selection
	const selectMachine = (machineName: string) => {
		onSelect(machineName);
		open = false;
	};

	// Get current group name
	$: currentGroupName = userGroups.find((g) => g.id === selectedGroupId)?.name || '';
</script>

<div bind:this={containerElement} class="relative {className}">
	{#if open}
		<div
			class="absolute bottom-full left-0 right-0 mb-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl shadow-lg max-h-80 overflow-hidden z-20"
			transition:slide={{ duration: 300, easing: quintOut, axis: 'y' }}
		>
			<!-- Group selector (only if multiple groups) -->
			{#if userGroups.length > 1}
				<div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
					<label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">
						{$i18n.t('Group')}:
					</label>
					<select
						bind:value={selectedGroupId}
						class="w-full px-3 py-1.5 text-sm bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-fixxit-primary"
					>
						{#each userGroups as group}
							<option value={group.id}>{group.name}</option>
						{/each}
					</select>
				</div>
			{/if}

			<!-- Machine list -->
			<div class="max-h-64 overflow-y-auto">
				{#if loading}
					<div class="px-4 py-8 flex justify-center">
						<Spinner className="size-6" />
					</div>
				{:else if error}
					<div class="px-4 py-3">
						<p class="text-sm text-red-600 dark:text-red-400 mb-2">
							{$i18n.t('Failed to load machines')}
						</p>
						<button
							on:click={() => loadEquipment(selectedGroupId)}
							class="text-sm text-fixxit-primary dark:text-fixxit-primary hover:underline"
						>
							{$i18n.t('Retry')}
						</button>
					</div>
				{:else if equipmentList.length === 0}
					<div class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 text-center">
						{$i18n.t('No machines available')}
					</div>
				{:else}
					{#each equipmentList as equipment, idx}
						<button
							class="w-full px-4 py-3 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-150 {idx <
							equipmentList.length - 1
								? 'border-b border-gray-100 dark:border-gray-750'
								: ''}"
							on:click={() => selectMachine(equipment.conventional_name)}
							role="option"
							title={equipment.conventional_name}
						>
							<span class="block overflow-hidden text-ellipsis whitespace-nowrap">
								{equipment.conventional_name}
							</span>
						</button>
					{/each}
				{/if}
			</div>
		</div>
	{/if}

	<!-- Collapsed bubble button -->
	<button
		class="w-full px-4 py-2 flex items-center justify-between bg-white/5 dark:bg-gray-500/5 border border-gray-100/30 dark:border-gray-850/30 hover:border-gray-200 dark:hover:border-gray-800 rounded-2xl shadow-md transition"
		on:click={() => (open = !open)}
		on:keydown={handleKeyDown}
		aria-label={$i18n.t('Select machine')}
		aria-expanded={open}
	>
		<div class="flex items-center gap-1">
			<span class="text-sm text-gray-700 dark:text-gray-300">
				{$i18n.t('Machines')}
			</span>
			{#if userGroups.length > 1 && currentGroupName}
				<span class="text-xs text-gray-500 dark:text-gray-400 opacity-70">
					({currentGroupName})
				</span>
			{/if}
		</div>
		{#if open}
			<ChevronUp className="size-4" strokeWidth="2" />
		{:else}
			<ChevronDown className="size-4" strokeWidth="2" />
		{/if}
	</button>
</div>
